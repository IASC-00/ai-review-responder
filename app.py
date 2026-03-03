import os
import anthropic
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

EXAMPLE_RESPONSE = {
    "reply": "Thank you so much for taking the time to share your experience, Sarah! We're thrilled to hear that you enjoyed your visit and that our team made you feel welcome. Your kind words mean the world to us. We look forward to seeing you again soon!",
    "tone": "Warm & Personal",
    "length": "Short",
    "tip": "Mentioning the reviewer's name and echoing a specific detail from their review increases the chance they'll return.",
    "is_demo": True
}

NEGATIVE_EXAMPLE_RESPONSE = {
    "reply": "Thank you for your honest feedback. We're sorry to hear your experience didn't meet your expectations — that's not the standard we hold ourselves to. We'd love the opportunity to make this right. Please reach out to us directly at [email] so we can look into this personally.",
    "tone": "Apologetic & Professional",
    "length": "Short",
    "tip": "Never get defensive in a public reply. Acknowledge, apologize briefly, then take the conversation offline.",
    "is_demo": True
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate-reply", methods=["POST"])
def generate_reply():
    data = request.get_json()
    review = (data.get("review") or "").strip()
    business_name = (data.get("business_name") or "our business").strip()
    business_type = (data.get("business_type") or "").strip()
    tone = (data.get("tone") or "professional").strip()

    if not review:
        return jsonify({"error": "Review text is required."}), 400

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        # Demo fallback
        if any(w in review.lower() for w in ["bad", "terrible", "awful", "worst", "horrible", "disappoint", "rude", "slow", "wrong", "never"]):
            return jsonify(NEGATIVE_EXAMPLE_RESPONSE)
        return jsonify(EXAMPLE_RESPONSE)

    sentiment = "positive" if not any(w in review.lower() for w in ["bad", "terrible", "awful", "worst", "horrible", "disappoint", "rude", "slow", "wrong", "never"]) else "negative/mixed"

    prompt = f"""You are a professional business response writer. Write a reply to this customer review for {business_name}{f', a {business_type}' if business_type else ''}.

Review:
{review}

Instructions:
- Tone: {tone}
- Keep it concise (2-4 sentences max)
- If positive: thank them sincerely, mention something specific from the review
- If negative/mixed: acknowledge the issue, apologize briefly, offer to resolve offline — never get defensive
- Do not use generic filler phrases like "we strive for excellence"
- Sound like a real human owner, not a corporate PR team

Also provide:
- The tone you used (e.g. "Warm & Personal", "Apologetic & Professional", "Friendly & Casual")
- A short 1-sentence tip for handling this type of review

Respond in this exact JSON format:
{{
  "reply": "...",
  "tone": "...",
  "tip": "..."
}}"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=os.environ.get("REPLY_MODEL", "claude-haiku-4-5-20251001"),
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = msg.content[0].text
        import json
        parsed = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
        parsed["is_demo"] = False
        return jsonify(parsed)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
