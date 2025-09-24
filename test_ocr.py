#!/usr/bin/env python3
"""
Test Mistral OCR API with Bhumi
"""
import asyncio
import os
import base64
from pathlib import Path
from bhumi.base_client import BaseLLMClient, LLMConfig
import dotenv 
dotenv.load_dotenv()
async def test_mistral_ocr():
    """Test Mistral OCR with the provided PDF file"""
    
    # Check for API key
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("❌ Please set MISTRAL_API_KEY environment variable")
        return
    
    # Path to the PDF file
    pdf_path = "/Users/rachpradhan/Downloads/Embecta FAQs - AI Text Replies (Updated 11 Sept 2025).pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print("🔍 Testing Mistral OCR API with Bhumi")
    print("=" * 50)
    
    # Create Mistral client
    config = LLMConfig(
        api_key=api_key,
        model="mistral/pixtral-12b-2409"  # Client model, not OCR model
    )
    client = BaseLLMClient(config)
    
    try:
        # Read and encode PDF file
        print(f"📄 Reading PDF: {Path(pdf_path).name}")
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
        
        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
        print(f"✅ PDF encoded ({len(pdf_base64)} chars)")
        
        # Test 1: Basic OCR
        print("\n1️⃣ Basic OCR Test")
        document = {
            "type": "file",
            "data": pdf_base64  # Remove mime_type - not allowed
        }
        
        result = await client.ocr(
            document=document,
            pages=[0],  # First page only
            include_image_base64=False
            # Don't specify model - let Mistral choose optimal OCR model
        )
        
        print(f"✅ OCR completed!")
        print(f"📊 Pages processed: {result.get('usage_info', {}).get('pages_processed', 'N/A')}")
        print(f"📄 Document size: {result.get('usage_info', {}).get('doc_size_bytes', 'N/A')} bytes")
        
        # Show extracted text (first 500 chars)
        if 'pages' in result and result['pages']:
            page_text = str(result['pages'][0])
            print(f"\n📝 Extracted text (first 500 chars):")
            print("-" * 50)
            print(page_text[:500] + "..." if len(page_text) > 500 else page_text)
        
        # Test 2: OCR with structured output
        print("\n2️⃣ OCR with Structured Output")
        
        # Define structured output schema for document analysis
        document_schema = {
            "type": "text",
            "json_schema": {
                "name": "document_analysis",
                "description": "Extract key information from FAQ document",
                "schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Document title"},
                        "company": {"type": "string", "description": "Company name"},
                        "document_type": {"type": "string", "description": "Type of document"},
                        "key_topics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Main topics covered"
                        }
                    },
                    "required": ["title", "document_type"]
                },
                "strict": False
            }
        }
        
        structured_result = await client.ocr(
            document=document,
            pages=[0],
            document_annotation_format=document_schema
            # Don't specify model - let Mistral choose
        )
        
        print("✅ Structured OCR completed!")
        if 'document_annotation' in structured_result:
            print(f"📋 Structured data: {structured_result['document_annotation']}")
        
        print("\n🎉 OCR tests completed successfully!")
        
    except Exception as e:
        print(f"❌ OCR test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mistral_ocr())
