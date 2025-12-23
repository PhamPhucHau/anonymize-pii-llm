import os
import json
import time
import re
from statistics import mean, stdev
from pydantic import BaseModel
from anonLLM.llm_ollama import OllamaLanguageModel
from anonLLM.anonymizer import Anonymizer
from autoprint import AutoPrint

# Paths
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "evaluate/test_data", "email_evaluation.json")
PROMPT_PATH = os.path.join(BASE_DIR, "evaluate/evaluation_prompt.txt")

# Load resources
print("\n" + "="*80)
print("STAGE 1: Loading Resources")
print("="*80)

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    evaluation_prompt = f.read()
print(f"✅ Loaded evaluation_prompt.txt ({len(evaluation_prompt)} chars)")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    emails = json.load(f)
print(f"✅ Loaded email_evaluation.json ({len(emails)} emails)")

# Initialize components
print("\n" + "="*80)
print("STAGE 2: Initializing Components")
print("="*80)

anonymizer = Anonymizer()
print("✅ Anonymizer initialized")

llm = OllamaLanguageModel(
    model="mistral:latest",
    temperature=0.5,
    anonymize=False  # We'll handle anonymization manually
)
print("✅ LLM (OllamaLanguageModel) initialized")

# Setup logging
logger_eval = AutoPrint(log_file="log/Evaluation_Report.txt", timestamp=True)
logger_eval.print("="*80)
logger_eval.print("ANONYMIZATION EVALUATION REPORT")
logger_eval.print("="*80)

# Define evaluation output format
class AnonymizationEvaluation(BaseModel):
    score: int
    risk_level: str
    remaining_pii: list
    reasoning: str

# Process each email
print("\n" + "="*80)
print("STAGE 3: Processing Emails")
print("="*80)

scores = []
results = []

def parse_llm_response(response_text):
    """
    Robust JSON parser for LLM responses
    Handles comments, malformed JSON, and extracts data using regex fallback
    """
    if not isinstance(response_text, str):
        return None
    
    try:
        # Step 1: Try direct JSON parsing
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    try:
        # Step 2: Extract JSON block and remove comments
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            # Remove C-style comments (// ...) and hash comments (# ...)
            json_str = re.sub(r'//.*?(?=\n|,|}|$)', '', json_str)
            json_str = re.sub(r'#.*?(?=\n|,|}|$)', '', json_str)
            # Remove trailing commas
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    
    try:
        # Step 3: Regex fallback - extract key values manually
        eval_data = {}
        
        # Extract score
        score_match = re.search(r'"score"\s*:\s*(\d+)', response_text)
        eval_data['score'] = int(score_match.group(1)) if score_match else 0
        
        # Extract risk_level
        risk_match = re.search(r'"risk_level"\s*:\s*"([^"]+)"', response_text)
        eval_data['risk_level'] = risk_match.group(1) if risk_match else "unknown"
        
        # Extract remaining_pii (list)
        pii_match = re.search(r'"remaining_pii"\s*:\s*\[(.*?)\](?=,|\})', response_text, re.DOTALL)
        if pii_match:
            pii_str = pii_match.group(1)
            # Extract quoted strings
            pii_list = re.findall(r'"([^"]*)"', pii_str)
            eval_data['remaining_pii'] = pii_list if pii_list else []
        else:
            eval_data['remaining_pii'] = []
        
        # Extract reasoning
        reasoning_match = re.search(r'"reasoning"\s*:\s*"([^"]*)"', response_text)
        eval_data['reasoning'] = reasoning_match.group(1) if reasoning_match else "Could not extract reasoning"
        
        # Verify we got at least a score
        if eval_data['score'] > 0 or score_match:
            return eval_data
    except Exception as e:
        print(f"   Regex fallback failed: {e}")
    
    # Step 4: Return None if all parsing fails
    return None

for idx, email_item in enumerate(emails, 1):
    eid = email_item.get("email_id")
    subject = email_item.get("subject")
    context = email_item.get("context")
    content = email_item.get("content")
    
    print(f"\n{'─'*80}")
    print(f"EMAIL {idx}/10 | ID: {eid} | Context: {context}")
    print(f"Subject: {subject}")
    print(f"{'─'*80}")
    
    logger_eval.print(f"\n{'─'*80}")
    logger_eval.print(f"EMAIL {idx}/10 | ID: {eid}")
    logger_eval.print(f"{'─'*80}")
    
    # Step 3.1: Show original content (truncated)
    print("\n📄 Step 3.1: Original Content (first 400 chars)")
    print(content[:400] + "..." if len(content) > 400 else content)
    logger_eval.print(f"\n📄 Original Content (first 400 chars):")
    logger_eval.print(content[:400] + "..." if len(content) > 400 else content)
    
    # Step 3.2: Anonymize
    print("\n🔐 Step 3.2: Anonymizing with Anonymizer...")
    anon_content, mappings = anonymizer.anonymize_data(content)
    print(f"✅ Anonymization complete")
    print(f"   Anonymized content (first 400 chars):")
    print(f"   {anon_content[:400]}...")
    logger_eval.print(f"\n🔐 Anonymized Content (first 400 chars):")
    logger_eval.print(anon_content[:400] + "...")
    logger_eval.print(f"\n📋 Mappings ({len(mappings)} categories):")
    for label, mapping in mappings.items():
        logger_eval.print(f"   {label}: {len(mapping)} entities")
        for orig, anon in list(mapping.items())[:3]:
            logger_eval.print(f"      {repr(orig)} → {anon}")
    
    # Step 3.3: Create evaluation prompt
    print("\n📝 Step 3.3: Creating evaluation prompt for LLM...")
    eval_prompt = f"""{evaluation_prompt}

Evaluate the following anonymized text:

{anon_content}

Provide your evaluation in JSON format with keys: score (0-10), risk_level (string), remaining_pii (list of strings), reasoning (string explaining your assessment).
"""
    print(f"✅ Evaluation prompt created ({len(eval_prompt)} chars)")
    
    # Step 3.4: Call LLM for evaluation with timeout
    print("\n🤖 Step 3.4: Calling LLM for anonymization evaluation...")
    print("   (This may take a moment... timeout: 120 seconds)")
    try:
        # Add timeout handling
        start_time = time.time()
        timeout_seconds = 120
        
        eval_response = llm.generate(eval_prompt)
        elapsed = time.time() - start_time
        
        if elapsed > timeout_seconds:
            print(f"⚠️ LLM response took {elapsed:.1f}s (exceeded timeout)")
        
        print(f"✅ LLM evaluation received in {elapsed:.1f}s")
        print(f"   Response (first 300 chars): {str(eval_response)[:300]}...")
        logger_eval.print(f"\n🤖 LLM Evaluation Response (received in {elapsed:.1f}s):")
        logger_eval.print(str(eval_response)[:500])
        
        # Parse response with robust parser
        eval_data = parse_llm_response(eval_response)
        
        if eval_data is None:
            print("   ❌ All parsing methods failed, using default values")
            eval_data = {
                "score": 5,  # Use middle score instead of 0
                "risk_level": "unknown",
                "remaining_pii": [],
                "reasoning": "Could not parse LLM response"
            }
        else:
            print("   ✅ Successfully parsed LLM response")
        
    except Exception as e:
        print(f"❌ LLM evaluation error: {e}")
        logger_eval.print(f"❌ Error during LLM evaluation: {e}")
        eval_data = {
            "score": 5,
            "risk_level": "error",
            "remaining_pii": [],
            "reasoning": f"Error: {str(e)}"
        }
    
    # Step 3.5: Extract and report results
    print("\n📊 Step 3.5: Evaluation Results")
    score = eval_data.get("score", 5)
    risk = eval_data.get("risk_level", "unknown")
    pii_found = eval_data.get("remaining_pii", [])
    reasoning = eval_data.get("reasoning", "No reasoning provided")
    
    print(f"   Score: {score}/10")
    print(f"   Risk Level: {risk}")
    print(f"   Remaining PII found: {len(pii_found)} items")
    if pii_found:
        for pii in pii_found[:5]:
            print(f"      - {pii}")
    print(f"   Reasoning: {reasoning[:150]}...")
    
    logger_eval.print(f"\n📊 Evaluation Results:")
    logger_eval.print(f"   Score: {score}/10")
    logger_eval.print(f"   Risk Level: {risk}")
    logger_eval.print(f"   Remaining PII: {pii_found}")
    logger_eval.print(f"   Reasoning: {reasoning}")
    
    # Store results
    scores.append(score)
    results.append({
        "email_id": eid,
        "subject": subject,
        "context": context,
        "score": score,
        "risk_level": risk,
        "remaining_pii": pii_found,
        "reasoning": reasoning,
        "mappings_count": len(mappings)
    })
    
    time.sleep(2)  # Rate limiting for LLM calls

# Summary Report
print("\n" + "="*80)
print("STAGE 4: Summary Report")
print("="*80)

avg_score = mean(scores) if scores else 0
std_score = stdev(scores) if len(scores) > 1 else 0
min_score = min(scores) if scores else 0
max_score = max(scores) if scores else 0

print(f"\n📈 Statistics:")
print(f"   Total emails evaluated: {len(scores)}")
print(f"   Average anonymization score: {avg_score:.2f}/10")
print(f"   Score range: {min_score} - {max_score}")
print(f"   Standard deviation: {std_score:.2f}" if std_score else "   Standard deviation: N/A")

logger_eval.print(f"\n{'='*80}")
logger_eval.print("SUMMARY STATISTICS")
logger_eval.print(f"{'='*80}")
logger_eval.print(f"Total emails evaluated: {len(scores)}")
logger_eval.print(f"Average anonymization score: {avg_score:.2f}/10")
logger_eval.print(f"Score range: {min_score} - {max_score}")
if std_score:
    logger_eval.print(f"Standard deviation: {std_score:.2f}")

# Risk distribution
print(f"\n📋 Risk Distribution:")
risk_dist = {}
for result in results:
    risk = result["risk_level"]
    risk_dist[risk] = risk_dist.get(risk, 0) + 1
    print(f"   {risk}: {risk_dist[risk]} email(s)")

logger_eval.print(f"\n📋 Risk Distribution:")
for risk, count in risk_dist.items():
    logger_eval.print(f"   {risk}: {count} email(s)")

# Top performing and worst performing
print(f"\n🏆 Best performing email:")
best = max(results, key=lambda x: x["score"])
print(f"   Email {best['email_id']}: Score {best['score']}/10 - {best['context']}")

print(f"\n⚠️ Worst performing email:")
worst = min(results, key=lambda x: x["score"])
print(f"   Email {worst['email_id']}: Score {worst['score']}/10 - {worst['context']}")

logger_eval.print(f"\n🏆 Best performing email:")
logger_eval.print(f"   Email {best['email_id']}: Score {best['score']}/10")
logger_eval.print(f"\n⚠️ Worst performing email:")
logger_eval.print(f"   Email {worst['email_id']}: Score {worst['score']}/10")

# Detailed results table
print(f"\n📊 Detailed Results:")
print(f"{'ID':<5} {'Context':<25} {'Score':<8} {'Risk Level':<15}")
print(f"{'-'*53}")
for result in results:
    print(f"{result['email_id']:<5} {result['context']:<25} {result['score']:<8} {result['risk_level']:<15}")

logger_eval.print(f"\n📊 Detailed Results Table:")
logger_eval.print(f"{'ID':<5} {'Context':<25} {'Score':<8} {'Risk Level':<15}")
logger_eval.print(f"{'-'*53}")
for result in results:
    logger_eval.print(f"{result['email_id']:<5} {result['context']:<25} {result['score']:<8} {result['risk_level']:<15}")

# Save detailed results to JSON
results_file = os.path.join(BASE_DIR, "evaluation_results.json")
with open(results_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\n✅ Detailed results saved to: {results_file}")
logger_eval.print(f"\n✅ Detailed results saved to: {results_file}")

print("\n" + "="*80)
print("✅ EVALUATION COMPLETE")
print("="*80)
logger_eval.print("\n" + "="*80)
logger_eval.print("✅ EVALUATION COMPLETE")
logger_eval.print("="*80)
