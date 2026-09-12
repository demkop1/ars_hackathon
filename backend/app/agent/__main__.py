"""Quick manual smoke test: `python -m app.agent` from backend/."""
from app.agent import ask, validate_interests

if __name__ == "__main__":
    print(ask("I have tonight free and love hands-on, playful stuff. Any ideas?"))
    print(validate_interests("I love live music and hands-on workshops"))
    print(validate_interests("asdkjhaskjdh 12321 !!!"))
