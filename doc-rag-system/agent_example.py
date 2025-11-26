"""
Example: Programming agent that uses RAG to work on Jira tickets.

This shows how to integrate the document RAG system with a programming agent.
"""

from pathlib import Path
from openai import OpenAI
from doc_retriever import DocumentRetriever


class ProgrammingAgent:
    """
    Programming agent that uses documentation context.
    """
    
    def __init__(
        self,
        doc_index_path: Path = Path("./doc_index"),
        model: str = "gpt-4o"
    ):
        """
        Initialize the agent.
        
        Args:
            doc_index_path: Path to document index
            model: OpenAI model to use
        """
        self.retriever = DocumentRetriever(db_path=doc_index_path)
        self.openai_client = OpenAI()
        self.model = model
    
    def work_on_ticket(
        self,
        ticket_description: str,
        code_context: str = "",
        top_k_docs: int = 5
    ) -> str:
        """
        Work on a Jira ticket using documentation context.
        
        Args:
            ticket_description: Description of the Jira ticket
            code_context: Optional code context (current file, etc.)
            top_k_docs: Number of docs to retrieve
            
        Returns:
            Agent's response with implementation plan
        """
        # Step 1: Retrieve relevant documentation
        print(f"🔍 Retrieving relevant documentation...")
        docs = self.retriever.retrieve(
            query=ticket_description,
            top_k=top_k_docs,
            use_graph=True,
            max_hops=2
        )
        
        if docs:
            print(f"✓ Found {len(docs)} relevant documents")
            for doc in docs:
                print(f"  - {doc.doc_title} (score: {doc.score:.3f})")
        else:
            print("⚠ No relevant documentation found")
        
        # Step 2: Format documentation for LLM
        doc_context = self.retriever.format_for_llm(docs) if docs else "No relevant documentation available."
        
        # Step 3: Build prompt
        prompt = self._build_prompt(ticket_description, code_context, doc_context)
        
        # Step 4: Call LLM
        print(f"\n💭 Generating implementation plan...")
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert programming agent. Use the provided documentation to implement solutions that follow the team's conventions and best practices."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    def _build_prompt(
        self,
        ticket: str,
        code_context: str,
        doc_context: str
    ) -> str:
        """Build the prompt for the LLM."""
        prompt_parts = [
            "# Jira Ticket",
            ticket,
            "",
            "# Relevant Documentation",
            doc_context,
        ]
        
        if code_context:
            prompt_parts.extend([
                "",
                "# Current Code Context",
                "```",
                code_context,
                "```"
            ])
        
        prompt_parts.extend([
            "",
            "# Task",
            "Based on the ticket description and the team's documentation:",
            "1. Explain how this should be implemented according to our conventions",
            "2. Identify which modules/files need changes",
            "3. Provide a detailed implementation plan",
            "4. Highlight any potential issues or considerations",
            "5. Reference specific documentation sections that are relevant",
            "",
            "Be specific and cite the documentation when making recommendations."
        ])
        
        return "\n".join(prompt_parts)
    
    def explain_code(
        self,
        code: str,
        question: str = "What does this code do?"
    ) -> str:
        """
        Explain code using documentation context.
        
        Args:
            code: Code to explain
            question: Specific question about the code
            
        Returns:
            Explanation
        """
        # Retrieve docs related to the code
        docs = self.retriever.retrieve(
            query=f"{question}\n\n{code[:500]}",  # Use code excerpt
            top_k=3,
            use_graph=True
        )
        
        doc_context = self.retriever.format_for_llm(docs) if docs else ""
        
        prompt = f"""# Code to Explain

```
{code}
```

# Question
{question}

# Relevant Documentation
{doc_context if doc_context else "No specific documentation found."}

# Task
Explain the code in the context of our codebase and conventions. Reference the documentation where relevant.
"""
        
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a code expert. Explain code clearly and reference documentation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content


def example_usage():
    """Example usage of the programming agent."""
    
    # Initialize agent
    agent = ProgrammingAgent(
        doc_index_path=Path("./doc_index"),
        model="gpt-4o"
    )
    
    # Example 1: Work on a Jira ticket
    ticket = """
    JIRA-123: Add rate limiting to payment API
    
    We need to add rate limiting to our payment processing endpoint to prevent abuse.
    The rate limit should be:
    - 100 requests per minute per user
    - 1000 requests per minute globally
    
    Return 429 status code when limit is exceeded.
    """
    
    print("=" * 80)
    print("EXAMPLE 1: Working on Jira Ticket")
    print("=" * 80)
    
    result = agent.work_on_ticket(ticket)
    print("\n" + result)
    
    # Example 2: Explain code
    code_sample = """
def process_payment(amount, card_token):
    if not validate_amount(amount):
        raise ValueError("Invalid amount")
    
    result = payment_gateway.charge(card_token, amount)
    
    if result.success:
        db.save_transaction(result)
        return result.transaction_id
    else:
        logger.error(f"Payment failed: {result.error}")
        raise PaymentError(result.error)
"""
    
    print("\n\n" + "=" * 80)
    print("EXAMPLE 2: Explaining Code")
    print("=" * 80)
    
    explanation = agent.explain_code(
        code_sample,
        question="How does our payment processing work? What are the conventions we follow?"
    )
    print("\n" + explanation)


if __name__ == '__main__':
    example_usage()
