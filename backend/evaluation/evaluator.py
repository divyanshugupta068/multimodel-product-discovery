import asyncio
import time
import json
from typing import List, Dict, Optional
from pathlib import Path
import numpy as np

from agents.product_discovery_agent import ProductDiscoveryAgent
from models.query import QueryRequest, QueryType
from .metrics import (
    EvaluationMetrics, LatencyMetrics, AccuracyMetrics, 
    CostMetrics, ModelComparisonMetrics, TestCase
)
from config import get_settings


class ProductDiscoveryEvaluator:
    """
    Comprehensive evaluation harness for the product discovery agent.
    Tests accuracy, latency, and cost across multiple scenarios.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.agent = ProductDiscoveryAgent()
        self.results = []
    
    async def run_evaluation(
        self,
        test_cases: List[TestCase],
        output_path: Optional[str] = None
    ) -> EvaluationMetrics:
        """
        Run full evaluation on provided test cases.
        
        Args:
            test_cases: List of test cases to evaluate
            output_path: Optional path to save results
            
        Returns:
            EvaluationMetrics with aggregated results
        """
        print(f"Starting evaluation with {len(test_cases)} test cases...")
        
        latencies = []
        accuracies = []
        costs = []
        passed = 0
        failed = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] Running: {test_case.name}")
            
            try:
                result = await self._run_single_test(test_case)
                self.results.append(result)
                
                if result["passed"]:
                    passed += 1
                    print(f"  ✓ PASSED")
                else:
                    failed += 1
                    print(f"  ✗ FAILED: {result.get('failure_reason', 'Unknown')}")
                
                # Collect metrics
                latencies.append(result["latency_ms"])
                accuracies.append(result.get("accuracy", 0.0))
                costs.append(result.get("cost", 0.0))
                
                # Show key metrics
                print(f"  Latency: {result['latency_ms']:.0f}ms")
                print(f"  Accuracy: {result.get('accuracy', 0)*100:.1f}%")
                print(f"  Cost: ${result.get('cost', 0):.4f}")
                
            except Exception as e:
                print(f"  ✗ ERROR: {str(e)}")
                failed += 1
                self.results.append({
                    "test_case": test_case.name,
                    "passed": False,
                    "error": str(e)
                })
        
        # Calculate aggregate metrics
        metrics = self._calculate_aggregate_metrics(
            test_cases,
            passed,
            failed,
            latencies,
            accuracies,
            costs
        )
        
        # Save results if output path provided
        if output_path:
            self._save_results(metrics, output_path)
        
        # Print summary
        self._print_summary(metrics)
        
        return metrics
    
    async def _run_single_test(self, test_case: TestCase) -> Dict:
        """Run a single test case and measure performance."""
        start_time = time.time()
        
        # Build query request from test case
        request = self._build_request(test_case)
        
        # Execute query
        response = await self.agent.process_query(request)
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Evaluate accuracy
        accuracy = self._evaluate_accuracy(test_case, response)
        
        # Estimate cost
        cost = response.cost_estimate or 0.0
        
        # Check if test passed
        passed = (
            latency_ms <= test_case.max_latency_ms and
            accuracy >= test_case.min_accuracy
        )
        
        failure_reason = None
        if not passed:
            reasons = []
            if latency_ms > test_case.max_latency_ms:
                reasons.append(f"Latency exceeded ({latency_ms:.0f}ms > {test_case.max_latency_ms}ms)")
            if accuracy < test_case.min_accuracy:
                reasons.append(f"Accuracy below threshold ({accuracy:.2%} < {test_case.min_accuracy:.2%})")
            failure_reason = "; ".join(reasons)
        
        return {
            "test_case": test_case.name,
            "passed": passed,
            "failure_reason": failure_reason,
            "latency_ms": latency_ms,
            "accuracy": accuracy,
            "cost": cost,
            "intent_matched": test_case.expected_intent == response.intent.value if test_case.expected_intent else None,
            "response": response.dict()
        }
    
    def _build_request(self, test_case: TestCase) -> QueryRequest:
        """Build QueryRequest from test case."""
        input_data = test_case.input_data
        
        return QueryRequest(
            query_text=input_data.get("query_text"),
            image_data=input_data.get("image_data"),
            audio_data=input_data.get("audio_data"),
            query_type=QueryType(test_case.query_type),
            max_results=input_data.get("max_results", 10)
        )
    
    def _evaluate_accuracy(self, test_case: TestCase, response) -> float:
        """
        Evaluate accuracy of response against expected output.
        Returns accuracy score between 0 and 1.
        """
        scores = []
        
        # Check intent accuracy
        if test_case.expected_intent:
            scores.append(1.0 if response.intent.value == test_case.expected_intent else 0.0)
        
        # Check if expected products are in results
        if test_case.expected_products and response.products:
            result_names = [p.product.name.lower() for p in response.products]
            matches = sum(
                1 for exp_name in test_case.expected_products
                if any(exp_name.lower() in name for name in result_names)
            )
            scores.append(matches / len(test_case.expected_products))
        
        # Check if any products returned (basic sanity check)
        if len(response.products) > 0:
            scores.append(1.0)
        else:
            scores.append(0.0)
        
        return np.mean(scores) if scores else 0.5
    
    def _calculate_aggregate_metrics(
        self,
        test_cases: List[TestCase],
        passed: int,
        failed: int,
        latencies: List[float],
        accuracies: List[float],
        costs: List[float]
    ) -> EvaluationMetrics:
        """Calculate aggregate metrics from test results."""
        
        # Latency metrics
        latency = LatencyMetrics(
            total_latency_ms=np.mean(latencies),
            vision_processing_ms=np.mean([r.get("response", {}).get("latency_breakdown", {}).get("vision_analysis", 0) 
                                          for r in self.results if "response" in r]),
            speech_processing_ms=np.mean([r.get("response", {}).get("latency_breakdown", {}).get("speech_transcription", 0) 
                                          for r in self.results if "response" in r]),
            tool_execution_ms=np.mean([r.get("response", {}).get("latency_breakdown", {}).get("tool_execution", 0) 
                                       for r in self.results if "response" in r])
        )
        
        # Accuracy metrics
        accuracy = AccuracyMetrics(
            product_identification_precision=np.mean(accuracies),
            intent_classification_accuracy=np.mean([
                1.0 if r.get("intent_matched") else 0.0 
                for r in self.results if r.get("intent_matched") is not None
            ])
        )
        
        # Cost metrics
        cost = CostMetrics(
            total_cost=np.sum(costs),
            cost_per_query=np.mean(costs) if costs else 0.0
        )
        
        return EvaluationMetrics(
            test_id=f"eval_{int(time.time())}",
            test_name="Product Discovery Evaluation",
            latency=latency,
            accuracy=accuracy,
            cost=cost,
            total_tests=len(test_cases),
            passed_tests=passed,
            failed_tests=failed,
            success_rate=passed / len(test_cases) if test_cases else 0.0,
            model_versions={
                "llm": self.settings.default_text_model,
                "vision": self.settings.default_vision_model,
                "embedding": self.settings.embedding_model
            }
        )
    
    def _save_results(self, metrics: EvaluationMetrics, output_path: str):
        """Save evaluation results to file."""
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metrics
        with open(output_path, 'w') as f:
            json.dump(metrics.dict(), f, indent=2, default=str)
        
        # Save detailed results
        results_path = output_path.replace('.json', '_detailed.json')
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n✓ Results saved to {output_path}")
        print(f"✓ Detailed results saved to {results_path}")
    
    def _print_summary(self, metrics: EvaluationMetrics):
        """Print evaluation summary."""
        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60)
        print(f"\nTests: {metrics.passed_tests}/{metrics.total_tests} passed ({metrics.success_rate:.1%})")
        print(f"\nLatency Metrics:")
        print(f"  Average Total: {metrics.latency.total_latency_ms:.0f}ms")
        print(f"  Target: <4000ms - {'✓ PASS' if metrics.latency.meets_target else '✗ FAIL'}")
        print(f"\nAccuracy Metrics:")
        if metrics.accuracy.product_identification_precision:
            print(f"  Product ID Precision: {metrics.accuracy.product_identification_precision:.1%}")
        if metrics.accuracy.intent_classification_accuracy:
            print(f"  Intent Classification: {metrics.accuracy.intent_classification_accuracy:.1%}")
        print(f"  Target: >85% - {'✓ PASS' if metrics.accuracy.meets_target else '✗ FAIL'}")
        print(f"\nCost Metrics:")
        print(f"  Cost per Query: ${metrics.cost.cost_per_query:.4f}")
        print(f"  Total Cost: ${metrics.cost.total_cost:.2f}")
        print(f"  Target: <$0.10 - {'✓ PASS' if metrics.cost.meets_target else '✗ FAIL'}")
        print(f"\nOverall: {'✓ ALL TARGETS MET' if metrics.overall_pass else '✗ SOME TARGETS MISSED'}")
        print("="*60)


async def main():
    """Example evaluation run."""
    evaluator = ProductDiscoveryEvaluator()
    
    # Define test cases
    test_cases = [
        TestCase(
            test_id="test_001",
            name="Text search - leather jacket",
            query_type="text",
            input_data={"query_text": "black leather jacket under $200"},
            expected_output={},
            expected_intent="search",
            expected_products=["Leather Jacket"],
            min_accuracy=0.8,
            max_latency_ms=3000
        ),
        TestCase(
            test_id="test_002",
            name="Text search - smartphone",
            query_type="text",
            input_data={"query_text": "iPhone 15 Pro"},
            expected_output={},
            expected_intent="search",
            expected_products=["iPhone"],
            min_accuracy=0.85,
            max_latency_ms=3000
        ),
        # Add more test cases...
    ]
    
    # Run evaluation
    metrics = await evaluator.run_evaluation(
        test_cases,
        output_path=evaluator.settings.eval_output_path + "results.json"
    )


if __name__ == "__main__":
    asyncio.run(main())
