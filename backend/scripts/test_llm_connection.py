import sys
from pathlib import Path

# Add backend directory to sys.path so we can import app
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.infrastructure.config.settings import settings
from app.infrastructure.ai.factory import create_llm_provider
from app.application.dto.enrichment_dto import ClinicAIInput, SignalSummary

def test_connection():
    print("=== Dental Radar LLM Connection Test ===")
    print(f"Configured Provider: {settings.ai_provider}")
    
    # Verify settings based on configured provider
    provider_name = settings.ai_provider.lower().strip()
    if provider_name == "gpt":
        print(f"Model: {settings.openai_model}")
        print(f"API Key: {'Configured (length: ' + str(len(settings.openai_api_key)) + ')' if settings.openai_api_key else 'NOT CONFIGURED'}")
    elif provider_name == "claude":
        print(f"Model: {settings.anthropic_model}")
        print(f"API Key: {'Configured (length: ' + str(len(settings.anthropic_api_key)) + ')' if settings.anthropic_api_key else 'NOT CONFIGURED'}")
    elif provider_name == "gemini":
        print(f"Model: {settings.gemini_model}")
        print(f"API Key: {'Configured (length: ' + str(len(settings.gemini_api_key)) + ')' if settings.gemini_api_key else 'NOT CONFIGURED'}")
    else:
        print(f"Error: Unknown provider '{provider_name}'")
        return

    try:
        print("\nInitializing LLM provider...")
        provider = create_llm_provider()
        
        print("Creating dummy clinic payload...")
        payload = ClinicAIInput(
            name="Test Dental Clinic",
            site_text="Welcome to Test Dental Clinic. We offer advanced orthodontics, implants, and digital teeth whitening. We use state of the art laser scanners.",
            services=["Orthodontics", "Implants", "Whitening"],
            signals=[
                SignalSummary(type="booking_system", evidence="Online appointment form found"),
                SignalSummary(type="active_socials", evidence="Instagram link found")
            ],
            rating=4.8,
            reviews=124,
            locations_count=2
        )
        
        print("Sending request to LLM (this may take a few seconds)...")
        completion = provider.analyze_clinic(payload)
        
        print("\n=== Success! ===")
        print(f"Provider used: {completion.provider}")
        print(f"Model used: {completion.model}")
        print(f"Prompt version: {completion.prompt_version}")
        print("\nEnriched Results:")
        print(f" - Growth Probability: {completion.result.growth_probability}%")
        print(f" - Technology Maturity: {completion.result.technology_maturity}%")
        print(f" - Marketing Sophistication: {completion.result.marketing_sophistication}%")
        print(f" - Expansion Probability: {completion.result.expansion_probability}%")
        print(f" - Explanation: {completion.result.explanation}")
        
    except Exception as e:
        print(f"\n=== Connection Failed! ===")
        print(f"Error details: {e}")
        print("\nMake sure your API key is correct and that your internet connection is active.")

if __name__ == "__main__":
    test_connection()
