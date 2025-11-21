import os

# If you want to enable AI filtering:
# Add OPENAI_API_KEY in Render environment variables.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def ai_approve(context: dict) -> bool:
    """
    context example:
    {
      "side": "SELL",
      "bias": "SELL",
      "rr": 2,
      "session": "NY",
      "spread": 0.25,
      "news_block": False
    }
    """

    # If no AI key → allow trade
    if not OPENAI_API_KEY:
        return True

    # Simple rules first
    side = context.get("side")
    bias = context.get("bias")
    news_block = context.get("news_block", False)

    # Reject during blocked news
    if news_block:
        return False

    # Reject if trade goes against bias
    if side and bias and side.upper() != bias.upper():
        return False

    # Otherwise allow 
    return True
