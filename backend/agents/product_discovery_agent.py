import time
import uuid
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from models.query import QueryRequest, QueryResponse, Intent, QueryType
from models.agent_state import AgentState, AgentStep, ConversationTurn
from models.product import ProductCard, ProductComparison
from vision.vision_orchestrator import VisionOrchestrator
from speech.speech_orchestrator import SpeechOrchestrator
from tools.product_search import ProductSearchTool
from tools.price_comparison import PriceComparisonTool
from tools.inventory_check import InventoryCheckTool
from tools.recommendation import RecommendationTool
from tools.review_analysis import ReviewAnalysisTool
from config import get_settings


class ProductDiscoveryAgent:
    """
    Main agent for multimodal product discovery using LangGraph.
    Orchestrates vision, speech, and tool execution for product queries.
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize LLMs
        self.llm = ChatOpenAI(
            model=self.settings.default_text_model,
            api_key=self.settings.openai_api_key,
            temperature=0.1
        )
        
        # Initialize processors and tools
        self.vision_orchestrator = VisionOrchestrator()
        self.speech_orchestrator = SpeechOrchestrator()
        self.search_tool = ProductSearchTool()
        self.price_tool = PriceComparisonTool()
        self.inventory_tool = InventoryCheckTool()
        self.recommendation_tool = RecommendationTool()
        self.review_tool = ReviewAnalysisTool()
        
        # Build agent graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build LangGraph workflow for product discovery.
        """
        workflow = StateGraph(AgentState)
        
        # Define nodes
        workflow.add_node("process_input", self._process_input)
        workflow.add_node("classify_intent", self._classify_intent)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("generate_response", self._generate_response)
        
        # Define edges
        workflow.set_entry_point("process_input")
        workflow.add_edge("process_input", "classify_intent")
        workflow.add_edge("classify_intent", "execute_tools")
        workflow.add_edge("execute_tools", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    async def process_query(self, request: QueryRequest) -> QueryResponse:
        """
        Process a multimodal query and return structured response.
        
        Args:
            request: QueryRequest with text/image/audio data
            
        Returns:
            QueryResponse with products and recommendations
        """
        start_time = time.time()
        query_id = str(uuid.uuid4())
        
        # Initialize agent state
        state = AgentState(
            session_id=request.session_id or str(uuid.uuid4()),
            user_id=request.user_id,
            current_query=request.query_text
        )
        
        # Store request context
        state.user_preferences = request.context or {}
        
        try:
            # Run through agent graph
            final_state = await self.graph.ainvoke(state, {"request": request})
            
            # Extract results
            products = final_state.tool_results.get("products", [])
            comparison = final_state.tool_results.get("comparison")
            purchase_action = final_state.tool_results.get("purchase_action")
            response_message = final_state.tool_results.get("message", "")
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Build response
            response = QueryResponse(
                query_id=query_id,
                intent=final_state.current_intent or Intent.SEARCH,
                intent_confidence=0.9,
                message=response_message,
                products=products,
                comparison=comparison,
                purchase_action=purchase_action,
                processing_time_ms=processing_time_ms,
                models_used=self._get_models_used(final_state),
                tool_calls=list(final_state.tool_results.keys()),
                latency_breakdown=final_state.step_timings,
                suggested_questions=self._generate_suggestions(final_state),
                cost_estimate=self._estimate_cost(final_state)
            )
            
            return response
            
        except Exception as e:
            # Error handling
            return QueryResponse(
                query_id=query_id,
                intent=Intent.SEARCH,
                intent_confidence=0.0,
                message=f"Error processing query: {str(e)}",
                products=[],
                processing_time_ms=(time.time() - start_time) * 1000,
                models_used={},
                tool_calls=[]
            )
    
    async def _process_input(self, state: AgentState, context: Dict[str, Any]) -> AgentState:
        """
        Process multimodal input (image/voice/text).
        """
        step_start = time.time()
        state.current_step = AgentStep.INPUT_PROCESSING
        
        request: QueryRequest = context["request"]
        
        # Process image if provided
        if request.image_data and self.settings.enable_vision_processing:
            state.current_step = AgentStep.VISION_ANALYSIS
            vision_result = await self.vision_orchestrator.analyze_with_best_model(
                request.image_data
            )
            state.vision_analysis = {
                "features": vision_result.visual_features.dict(),
                "identification": vision_result.product_identification.dict(),
                "queries": vision_result.search_queries
            }
            # Use vision-generated query if no text provided
            if not request.query_text:
                state.current_query = vision_result.search_query
        
        # Process audio if provided
        if request.audio_data and self.settings.enable_speech_processing:
            state.current_step = AgentStep.SPEECH_TRANSCRIPTION
            speech_result = await self.speech_orchestrator.process_voice_command(
                request.audio_data
            )
            state.speech_transcription = {
                "text": speech_result.transcription.text,
                "intent": speech_result.intent,
                "entities": speech_result.entities,
                "confidence": speech_result.confidence
            }
            # Use transcribed text if no text provided
            if not request.query_text:
                state.current_query = speech_result.transcription.text
        
        # Use text query if provided
        if request.query_text:
            state.current_query = request.query_text
        
        step_time = (time.time() - step_start) * 1000
        state.record_step_time(AgentStep.INPUT_PROCESSING, step_time)
        
        return state
    
    async def _classify_intent(self, state: AgentState, context: Dict[str, Any]) -> AgentState:
        """
        Classify user intent from query.
        """
        step_start = time.time()
        state.current_step = AgentStep.INTENT_CLASSIFICATION
        
        # Check if intent already determined from speech
        if state.speech_transcription and state.speech_transcription.get("intent"):
            intent_str = state.speech_transcription["intent"]
            state.current_intent = Intent(intent_str)
        else:
            # Classify intent using LLM
            intent_str = await self._classify_with_llm(state.current_query)
            state.current_intent = Intent(intent_str)
        
        step_time = (time.time() - step_start) * 1000
        state.record_step_time(AgentStep.INTENT_CLASSIFICATION, step_time)
        
        return state
    
    async def _execute_tools(self, state: AgentState, context: Dict[str, Any]) -> AgentState:
        """
        Execute appropriate tools based on intent.
        """
        step_start = time.time()
        state.current_step = AgentStep.TOOL_EXECUTION
        
        request: QueryRequest = context["request"]
        intent = state.current_intent
        
        # Execute tools based on intent
        if intent == Intent.SEARCH:
            products = self.search_tool.search(
                query=state.current_query,
                filters=request.filters.dict() if request.filters else None,
                max_results=request.max_results
            )
            state.tool_results["products"] = products
        
        elif intent == Intent.COMPARE:
            # Extract product IDs from query or use search results
            products = self.search_tool.search(
                query=state.current_query,
                max_results=5
            )
            if len(products) >= 2:
                comparison = self._create_comparison([p.product for p in products[:3]])
                state.tool_results["comparison"] = comparison
                state.tool_results["products"] = products
        
        elif intent == Intent.PRICE_CHECK:
            products = self.search_tool.search(
                query=state.current_query,
                max_results=5
            )
            if products:
                price_comparison = self.price_tool.compare_prices(products[0].product.id)
                state.tool_results["price_comparison"] = price_comparison
                state.tool_results["products"] = products
        
        elif intent == Intent.AVAILABILITY_CHECK:
            products = self.search_tool.search(
                query=state.current_query,
                max_results=5
            )
            if products:
                availability = self.inventory_tool.check_availability(products[0].product.id)
                state.tool_results["availability"] = availability
                state.tool_results["products"] = products
        
        elif intent == Intent.RECOMMENDATION:
            recommendations = self.recommendation_tool.get_recommendations(
                user_id=state.user_id,
                session_id=state.session_id,
                context=state.user_preferences,
                max_results=request.max_results
            )
            state.tool_results["products"] = recommendations
        
        elif intent == Intent.REVIEW_ANALYSIS:
            products = self.search_tool.search(
                query=state.current_query,
                max_results=1
            )
            if products:
                review_summary = self.review_tool.analyze_reviews(products[0].product.id)
                state.tool_results["review_summary"] = review_summary
                state.tool_results["products"] = products
        
        step_time = (time.time() - step_start) * 1000
        state.record_step_time(AgentStep.TOOL_EXECUTION, step_time)
        
        return state
    
    async def _generate_response(self, state: AgentState, context: Dict[str, Any]) -> AgentState:
        """
        Generate natural language response.
        """
        step_start = time.time()
        state.current_step = AgentStep.RESPONSE_GENERATION
        
        # Generate conversational response using LLM
        message = await self._generate_message_with_llm(state)
        state.tool_results["message"] = message
        
        step_time = (time.time() - step_start) * 1000
        state.record_step_time(AgentStep.RESPONSE_GENERATION, step_time)
        state.current_step = AgentStep.COMPLETE
        
        return state
    
    async def _classify_with_llm(self, query: str) -> str:
        """
        Classify intent using LLM.
        """
        prompt = f"""Classify the following product query into one of these intents:
        - search: Looking for products
        - compare: Comparing multiple products
        - purchase: Ready to buy
        - question: Asking about product details
        - recommendation: Seeking recommendations
        - price_check: Checking prices
        - availability_check: Checking stock/availability
        - review_analysis: Looking for reviews/ratings
        
        Query: {query}
        
        Respond with only the intent name."""
        
        response = await self.llm.ainvoke(prompt)
        intent = response.content.strip().lower()
        
        # Validate intent
        valid_intents = [i.value for i in Intent]
        if intent in valid_intents:
            return intent
        return "search"  # Default fallback
    
    async def _generate_message_with_llm(self, state: AgentState) -> str:
        """
        Generate conversational response using LLM.
        """
        products = state.tool_results.get("products", [])
        comparison = state.tool_results.get("comparison")
        
        product_summary = "\n".join([
            f"- {p.product.name}: ${p.product.best_price.amount if p.product.best_price else 'N/A'}"
            for p in products[:5]
        ])
        
        prompt = f"""Generate a helpful, conversational response for this product query.
        
        Query: {state.current_query}
        Intent: {state.current_intent.value}
        
        Found products:
        {product_summary}
        
        Generate a natural response (2-3 sentences) that:
        1. Acknowledges what the user is looking for
        2. Summarizes the key findings
        3. Offers to help further if needed
        """
        
        response = await self.llm.ainvoke(prompt)
        return response.content.strip()
    
    def _create_comparison(self, products: List) -> ProductComparison:
        """
        Create product comparison object.
        """
        from models.product import ProductComparison
        
        if len(products) < 2:
            return None
        
        # Build comparison table
        comparison_table = {
            "Name": [p.name for p in products],
            "Brand": [p.features.brand or "N/A" for p in products],
            "Price": [f"${p.best_price.amount}" if p.best_price else "N/A" for p in products],
            "Category": [p.category.value for p in products]
        }
        
        return ProductComparison(
            products=products,
            comparison_table=comparison_table,
            key_differences=["Price", "Brand", "Features"]
        )
    
    def _get_models_used(self, state: AgentState) -> Dict[str, str]:
        """Extract which models were used in processing."""
        models = {"llm": self.settings.default_text_model}
        
        if state.vision_analysis:
            models["vision"] = self.settings.default_vision_model
        if state.speech_transcription:
            models["speech"] = "whisper-1"
        
        return models
    
    def _generate_suggestions(self, state: AgentState) -> List[str]:
        """Generate follow-up suggestions."""
        suggestions = []
        
        if state.current_intent == Intent.SEARCH:
            suggestions = [
                "Compare top 3 products",
                "Check price across retailers",
                "Show customer reviews"
            ]
        elif state.current_intent == Intent.COMPARE:
            suggestions = [
                "Check availability",
                "Show detailed specifications",
                "Find similar products"
            ]
        
        return suggestions[:3]
    
    def _estimate_cost(self, state: AgentState) -> float:
        """Estimate API cost for the query."""
        # Simplified cost estimation
        cost = 0.0
        
        if state.vision_analysis:
            cost += 0.01  # GPT-4V cost per image
        if state.speech_transcription:
            cost += 0.006  # Whisper cost per minute (estimate)
        
        # LLM costs
        cost += 0.01  # Intent classification + response generation
        
        return round(cost, 3)
