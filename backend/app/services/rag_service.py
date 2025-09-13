import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

# Core LangChain and LangGraph components
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

from app.services.llm_service import get_llm
from app.services.db_service import get_pinecone_service
from app.core.config import settings
from langchain_core.documents import Document

# A simple state for our graph
class AgentState(TypedDict):
    messages: List[HumanMessage | AIMessage]
    documents: List[Document]  # ✅ add this
    role: str
    tech_stack: List[str]
    difficulty: str
    session_id: str

class RAGService:
    def __init__(self):
        self.llm = get_llm()
        self.retriever = get_pinecone_service().get_retriever()
        self.rag_chain = self._setup_rag_chain()
        self.fallback_chain = self._setup_fallback_chain()
        self.agent_executor = self._setup_agent_executor()

    def _setup_rag_chain(self):
        """Builds the RAG chain for when documents are found."""
        rag_prompt = ChatPromptTemplate.from_messages([
            ("system",
            "You are an expert technical interviewer. "
            "From the retrieved context below, pick or reformulate **one clear interview question only**. "
            "Do not include answers. If no context is useful, create a beginner-friendly question about the given role/tech stack. "
            "\n\nContext:\n{context}"),
            ("human", "Generate a question for: {question}")
        ])
        return rag_prompt | self.llm | StrOutputParser()

    def _setup_fallback_chain(self):
        """Builds a simple chain for when RAG retrieval fails."""
        fallback_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI interviewer. Your task is to ask one brief, introductory question about Python programming based on the user's message."),
            ("human", "{question}")
        ])
        return fallback_prompt | self.llm | StrOutputParser()

    def _retrieve_documents(self, state):
        """Node to retrieve documents from Pinecone with metadata filtering."""
        role = state.get("role")
        tech_stack = state.get("tech_stack", [])
        difficulty = state.get("difficulty", None)

        # Build metadata filter dynamically (skip nulls)
        metadata_filter = {}
        if role:
            metadata_filter["role"] = role
        if difficulty:
            metadata_filter["difficulty"] = difficulty
        if tech_stack:
            metadata_filter["skill"] = {"$in": tech_stack}

        query = state["messages"][-1].content

        documents = self.retriever.invoke(
            query,
            filter=metadata_filter if metadata_filter else None
        )

        if not documents:
            return {"messages": [HumanMessage(content=query)], "documents": []}
        return {"messages": [HumanMessage(content=query)], "documents": documents}


    def _route_chain(self, state):
        """Conditional router to choose between RAG and Fallback."""
        # Use RunnableLambda to get the documents from the state
        documents = state.get("documents", [])
        if documents:
            print("Router: Documents found. Using RAG chain.")
            return "rag"
        else:
            print("Router: No documents found. Using fallback chain.")
            return "fallback"
        

    def _generate_rag_response(self, state):
        user_message = state["messages"][-1].content
        documents = state["documents"]

        # Convert retrieved documents into plain text context
        if documents:
            context_text = "\n\n".join([
                f"{doc.page_content}\n"
                f"(Role: {doc.metadata.get('role')}, "
                f"Skill: {doc.metadata.get('skill')}, "
                f"Difficulty: {doc.metadata.get('difficulty')})"
                for doc in documents
            ])
        else:
            context_text = "No relevant documents found."

        # 🔍 Send raw context to LLM (skip StrOutputParser first)
        response = self.llm.invoke(
            f"You are an expert interviewer. Using this context, generate ONE interview question only.\n\n"
            f"Context:\n{context_text}\n\nUser request: {user_message}"
        )

        print("DEBUG - Raw Gemini output:", response)

        # Extract plain text safely
        if hasattr(response, "content"):
            final_text = response.content
        else:
            final_text = str(response)

        return {"messages": [AIMessage(content=final_text or "No question generated.")]}



        
    def _generate_fallback_response(self, state):
        user_message = state["messages"][-1].content
        response = self.fallback_chain.invoke({"question": user_message})
        return {"messages": [AIMessage(content=response)]}

    def _setup_agent_executor(self):
        """Builds the LangGraph workflow with a conditional router."""
        workflow = StateGraph(AgentState)
        
        # Define nodes
        workflow.add_node("retrieve", self._retrieve_documents)
        workflow.add_node("rag_node", self._generate_rag_response)
        workflow.add_node("fallback_node", self._generate_fallback_response)
        
        # Define edges
        workflow.set_entry_point("retrieve")
        workflow.add_conditional_edges(
            "retrieve",
            self._route_chain,
            {"rag": "rag_node", "fallback": "fallback_node"}
        )
        workflow.add_edge("rag_node", END)
        workflow.add_edge("fallback_node", END)
        
        return workflow.compile()

    async def get_response(self, role: str, tech_stack: list, difficulty: str, session_id: str):
        initial_state = {
            "messages": [HumanMessage(content=f"Generate interview questions for {role} using {', '.join(tech_stack)}")],
            "role": role,
            "tech_stack": tech_stack,
            "difficulty": difficulty,
            "session_id": session_id
        }

        # ✅ Use invoke instead of stream
        result = self.agent_executor.invoke(initial_state)
        print("DEBUG - Final Agent Executor Result:", result)  # 👀 for debugging

        # Extract AIMessage content
        messages = result.get("messages", [])
        for message in messages:
            if isinstance(message, AIMessage) and message.content.strip():
                return message.content.strip()

        return "No question generated."
