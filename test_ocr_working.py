#!/usr/bin/env python3
"""
Working Mistral OCR Test with File Upload
"""
import asyncio
import os
from bhumi.base_client import BaseLLMClient, LLMConfig
import dotenv
dotenv.load_dotenv()

async def test_mistral_ocr_complete():
    """Complete OCR test with file upload and processing"""
    
    # Check for API key
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("❌ Please set MISTRAL_API_KEY environment variable")
        return
    
    pdf_path = "/Users/rachpradhan/Downloads/Embecta FAQs - AI Text Replies (Updated 11 Sept 2025).pdf"
    
    print("🔍 Testing Complete Mistral OCR Workflow")
    print("=" * 50)
    
    # Create Mistral client
    config = LLMConfig(
        api_key=api_key,
        model="mistral/pixtral-12b-2409"  # Client model
    )
    client = BaseLLMClient(config)
    
    try:
        # Step 1: Upload the PDF file
        print("📤 Step 1: Uploading PDF file...")
        upload_result = await client.upload_file(pdf_path, purpose="ocr")
        file_id = upload_result["id"]
        print(f"✅ File uploaded successfully!")
        print(f"   File ID: {file_id}")
        print(f"   Size: {upload_result['bytes']} bytes")
        print(f"   Filename: {upload_result['filename']}")
        
        # Step 2: Run OCR on the uploaded file
        print("\n🔍 Step 2: Running OCR on uploaded file...")
        ocr_result = await client.ocr(
            document={
                "type": "file",
                "file_id": file_id
            },
            model="mistral-ocr-latest",
            pages=[0, 1]  # First two pages
        )
        
        print("✅ OCR completed successfully!")
        print(f"📊 Pages processed: {ocr_result['usage_info']['pages_processed']}")
        print(f"📄 Document size: {ocr_result['usage_info']['doc_size_bytes']} bytes")
        print(f"🤖 Model used: {ocr_result['model']}")
        
        # Step 3: Display extracted content
        print("\n📝 Step 3: Extracted Content")
        print("=" * 50)
        
        for i, page in enumerate(ocr_result["pages"]):
            print(f"\n📄 Page {page['index'] + 1}:")
            print(f"   Dimensions: {page['dimensions']['width']}x{page['dimensions']['height']} @ {page['dimensions']['dpi']} DPI")
            print(f"   Images found: {len(page['images'])}")
            
            # Show extracted text (first 800 characters)
            markdown_content = page["markdown"]
            print(f"\n📝 Extracted Text (first 800 chars):")
            print("-" * 60)
            print(markdown_content[:800] + "..." if len(markdown_content) > 800 else markdown_content)
        
        # Step 4: OCR with structured output
        print("\n🏗️ Step 4: OCR with Structured Output")
        print("=" * 50)
        
        # Define schema for FAQ extraction
        faq_schema = {
            "type": "text",
            "json_schema": {
                "name": "faq_extraction",
                "description": "Extract FAQ information from document",
                "schema": {
                    "type": "object",
                    "properties": {
                        "document_title": {"type": "string", "description": "Title of the document"},
                        "company_name": {"type": "string", "description": "Company name"},
                        "faq_topics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of FAQ topics covered"
                        },
                        "video_links": {
                            "type": "array", 
                            "items": {"type": "string"},
                            "description": "YouTube or video links found"
                        },
                        "key_health_advice": {
                            "type": "array",
                            "items": {"type": "string"}, 
                            "description": "Key health advice or warnings"
                        }
                    },
                    "required": ["document_title", "faq_topics"]
                },
                "strict": False
            }
        }
        
        structured_result = await client.ocr(
            document={
                "type": "file",
                "file_id": file_id
            },
            model="mistral-ocr-latest",
            pages=[0],  # First page only for structured extraction
            document_annotation_format=faq_schema
        )
        
        print("✅ Structured OCR completed!")
        if structured_result.get("document_annotation"):
            print(f"📋 Structured Data:")
            print(f"   {structured_result['document_annotation']}")
        
        print("\n🎉 Complete OCR workflow successful!")
        
    except Exception as e:
        print(f"❌ OCR workflow failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mistral_ocr_complete())
