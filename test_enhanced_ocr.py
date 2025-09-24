#!/usr/bin/env python3
"""
Test Enhanced OCR API with Dual Workflows
"""
import asyncio
import os
from bhumi.base_client import BaseLLMClient, LLMConfig
import dotenv
dotenv.load_dotenv()

async def test_enhanced_ocr():
    """Test the enhanced OCR API with both workflows"""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("❌ Please set MISTRAL_API_KEY environment variable")
        return
    
    pdf_path = "/Users/rachpradhan/Downloads/Embecta FAQs - AI Text Replies (Updated 11 Sept 2025).pdf"
    
    print("🔍 Testing Enhanced OCR API")
    print("=" * 50)
    
    client = BaseLLMClient(LLMConfig(api_key=api_key, model="mistral/pixtral-12b-2409"))
    
    try:
        # Test Workflow 1: Direct file upload + OCR (New Enhanced API)
        print("\n1️⃣ Workflow 1: Direct file upload + OCR")
        result1 = await client.ocr(
            file_path=pdf_path,
            pages=[0],
            model="mistral-ocr-latest"
        )
        
        print(f"✅ Direct workflow completed!")
        print(f"📄 Pages processed: {result1['usage_info']['pages_processed']}")
        print(f"📝 Text preview: {result1['pages'][0]['markdown'][:200]}...")
        
        # Test Workflow 2: Pre-uploaded file (Existing API)
        print("\n2️⃣ Workflow 2: Pre-uploaded file")
        upload_result = await client.upload_file(pdf_path, purpose="ocr")
        result2 = await client.ocr(
            document={"type": "file", "file_id": upload_result["id"]},
            pages=[0]
        )
        
        print(f"✅ Pre-upload workflow completed!")
        print(f"📄 Pages processed: {result2['usage_info']['pages_processed']}")
        print(f"📝 Text preview: {result2['pages'][0]['markdown'][:200]}...")
        
        # Test error handling
        print("\n3️⃣ Error Handling Test")
        try:
            # This should fail - can't specify both
            await client.ocr(
                file_path=pdf_path,
                document={"type": "file", "file_id": "test"},
                pages=[0]
            )
        except ValueError as e:
            print(f"✅ Error handling works: {e}")
        
        print("\n🎉 Enhanced OCR API tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_ocr())
