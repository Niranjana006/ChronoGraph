# evaluation/evaluate.py
import os
import asyncio
import pandas as pd
from datasets import Dataset

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

from app.config import settings
from evaluation.benchmark_dataset import BENCHMARK_DATASET
from evaluation.baseline_rag import run_baseline_rag
from evaluation.chronos_runner import run_chronos_rag

# Initialize the LLM (Groq via Llama 3)
llm = ChatOpenAI(
    model=settings.llm_model,
    api_key=settings.llm_api_key,
    base_url="https://api.groq.com/openai/v1",
    max_retries=5,
    temperature=0.0
)

# --- CUSTOM RAGAS-STYLE METRICS ---

async def score_faithfulness(question: str, answer: str, contexts: list[str]) -> float:
    """
    RAGAS Faithfulness: Does the answer claim things that aren't in the context?
    """
    context_str = "\n".join(contexts)
    prompt = f"""
    Context:
    {context_str}
    
    Question: {question}
    System Answer: {answer}
    
    Is the System Answer completely faithful to the provided context? 
    If the answer claims ANY facts that are not supported by the context, or if it hallucinates, output 0.0.
    If the answer only makes claims supported by the context, or correctly states that the context is contradictory without inventing new facts, output 1.0.
    Output ONLY a single float number (0.0 or 1.0).
    """
    try:
        response = await llm.ainvoke(prompt)
        val = float(response.content.strip())
        return min(max(val, 0.0), 1.0)
    except Exception as e:
        print(f"Error in score_faithfulness: {e}")
        return 0.0

async def score_answer_relevancy(question: str, answer: str) -> float:
    """
    RAGAS Answer Relevancy: Does the answer address the question?
    """
    prompt = f"""
    Question: {question}
    System Answer: {answer}
    
    Does the System Answer address the user's Question?
    If the answer is a direct, relevant response (even if it points out a contradiction), output 1.0.
    If the answer is completely off-topic or fails to address the question, output 0.0.
    If it's partially relevant, you can output 0.5.
    Output ONLY a single float number between 0.0 and 1.0.
    """
    try:
        response = await llm.ainvoke(prompt)
        val = float(response.content.strip())
        return min(max(val, 0.0), 1.0)
    except Exception as e:
        print(f"Error in score_answer_relevancy: {e}")
        return 0.0

async def score_contradiction_awareness(question: str, answer: str, ground_truth: str) -> float:
    """
    Custom Metric: Did the system warn the user about the contradiction?
    """
    prompt = f"""
    Query: {question}
    Ground Truth expected behavior: {ground_truth}
    System Answer: {answer}
    
    Did the system answer correctly acknowledge the conflicting/contradictory information? 
    Score 1.0 if it clearly warned the user of the contradiction and presented both sides. 
    Score 0.0 if it confidently picked one side without acknowledging the other, or failed to answer.
    Output ONLY a single float number between 0.0 and 1.0.
    """
    try:
        response = await llm.ainvoke(prompt)
        val = float(response.content.strip())
        return min(max(val, 0.0), 1.0)
    except Exception as e:
        print(f"Error in score_contradiction_awareness: {e}")
        return 0.0

async def main():
    from app.graph.neo4j_client import neo4j_client
    await neo4j_client.connect()
    
    results_baseline = []
    results_chronos = []

    print(f"Running evaluation on {len(BENCHMARK_DATASET)} synthetic test cases...")
    for i, item in enumerate(BENCHMARK_DATASET):
        print(f"\n--- Testing Case: {item['id']} ({item['domain']}) ---")
        query = item["query"]
        doc1 = item["doc1"]
        doc2 = item["doc2"]
        gt = item["ground_truth"]
        
        try:
            print("Running Baseline RAG...")
            baseline_ans = await run_baseline_rag(query, doc1, doc2)
            print("Baseline Answer:", baseline_ans)
            
            print("Running ChronosGraph RAG...")
            chronos_ans = await run_chronos_rag(query, doc1, doc2)
            print("Chronos Answer:", chronos_ans)
            
            # Calculate Metrics
            print("Calculating RAGAS metrics for Baseline...")
            b_faith = await score_faithfulness(query, baseline_ans, [doc1, doc2])
            b_rel = await score_answer_relevancy(query, baseline_ans)
            b_ca = await score_contradiction_awareness(query, baseline_ans, gt)
            
            print("Calculating RAGAS metrics for ChronosGraph...")
            c_faith = await score_faithfulness(query, chronos_ans, [doc1, doc2])
            c_rel = await score_answer_relevancy(query, chronos_ans)
            c_ca = await score_contradiction_awareness(query, chronos_ans, gt)
        except Exception as e:
            print(f"Error during evaluation of case {item['id']}: {e}")
            print("Stopping evaluation due to error (e.g. rate limit). Saving progress...")
            break

        results_baseline.append({
            "faithfulness": b_faith,
            "answer_relevancy": b_rel,
            "contradiction_awareness": b_ca
        })
        
        results_chronos.append({
            "faithfulness": c_faith,
            "answer_relevancy": c_rel,
            "contradiction_awareness": c_ca
        })
        
        # Incremental Save
        df_baseline = pd.DataFrame(results_baseline)
        df_chronos = pd.DataFrame(results_chronos)
        summary = {
            "Metric": ["Faithfulness", "Answer Relevancy", "Contradiction Awareness"],
            "Baseline (Query-Time Only)": [
                df_baseline["faithfulness"].mean(),
                df_baseline["answer_relevancy"].mean(),
                df_baseline["contradiction_awareness"].mean()
            ],
            "ChronosGraph (Scoped Auditing)": [
                df_chronos["faithfulness"].mean(),
                df_chronos["answer_relevancy"].mean(),
                df_chronos["contradiction_awareness"].mean()
            ]
        }
        summary_df = pd.DataFrame(summary)
        with open("evaluation_results.md", "w") as f:
            f.write(f"# Phase 7 Evaluation: Detection-Coverage Comparison (Completed {i+1}/{len(BENCHMARK_DATASET)})\n\n")
            cols = summary_df.columns.tolist()
            f.write("| " + " | ".join(cols) + " |\n")
            f.write("|" + "|".join(["---"] * len(cols)) + "|\n")
            for _, row in summary_df.iterrows():
                f.write("| " + " | ".join(str(x) for x in row.values) + " |\n")

    print("\n" + "="*50)
    print("EVALUATION RESULTS")
    print("="*50)
    if 'summary_df' in locals():
        print(summary_df.to_string(index=False))
        print(f"\nResults written to evaluation_results.md ({len(results_baseline)} cases evaluated)")
    else:
        print("No cases completed.")

if __name__ == "__main__":
    asyncio.run(main())
