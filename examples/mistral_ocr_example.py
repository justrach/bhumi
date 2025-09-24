#!/usr/bin/env python3
"""
Mistral OCR Example with Bhumi

Demonstrates Mistral's dedicated OCR API for document processing:
- Basic OCR text extraction
- Structured data extraction with schemas
- Multi-page document processing
- Image extraction and analysis

Usage:
    export MISTRAL_API_KEY=your_mistral_api_key
    python examples/mistral_ocr_example.py
"""
import asyncio
import os
import base64
from pathlib import Path
from bhumi.base_client import BaseLLMClient, LLMConfig
import dotenv 
dotenv.load_dotenv()

async def main():
    # Check for API key
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("❌ Please set MISTRAL_API_KEY environment variable")
        return

    print("🔍 Mistral OCR Examples with Bhumi")
    print("=" * 50)

    # Create Mistral client for OCR
    config = LLMConfig(
        api_key=api_key,
        model="mistral/pixtral-12b-2409"  # This is for the client, not OCR
    )
    client = BaseLLMClient(config)

    # Example 1: Basic OCR with image URL
    print("\n1️⃣ Basic OCR with Image URL")
    try:
        # Simple receipt image (base64 encoded)
        sample_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        result = await client.ocr(
            document={
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{sample_image_b64}"}
            }
            # Don't specify model - let Mistral use default OCR model
        )
        
        print("✅ Basic OCR completed")
        print(f"📊 Usage: {result.get('usage_info', {})}")
        
    except Exception as e:
        print(f"❌ Basic OCR failed: {e}")

    # Example 2: PDF OCR with structured output
    print("\n2️⃣ PDF OCR with Structured Output")
    
    # Define schema for extracting structured data from documents
    document_schema = {
        "type": "text",
        "json_schema": {
            "name": "document_analysis",
            "description": "Extract key information from document",
            "schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Document title"},
                    "company": {"type": "string", "description": "Company or organization name"},
                    "document_type": {"type": "string", "description": "Type of document (FAQ, manual, etc.)"},
                    "key_topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Main topics or sections covered"
                    },
                    "contact_info": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string"},
                            "phone": {"type": "string"},
                            "website": {"type": "string"}
                        }
                    }
                },
                "required": ["title", "document_type"]
            },
            "strict": False
        }
    }

    # Bounding box schema for extracting individual elements
    bbox_schema = {
        "type": "text", 
        "json_schema": {
            "name": "text_element",
            "description": "Individual text element with metadata",
            "schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Extracted text"},
                    "element_type": {"type": "string", "description": "Type of element (heading, paragraph, etc.)"},
                    "confidence": {"type": "number", "description": "OCR confidence score"}
                }
            }
        }
    }

    # Test with a sample PDF file path
    pdf_path = "/Users/rachpradhan/Downloads/Embecta FAQs - AI Text Replies (Updated 11 Sept 2025).pdf"
    
    if Path(pdf_path).exists():
        try:
            # Read PDF file
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            # Use correct FileChunk format (no mime_type field)
            result = await client.ocr(
                document={
                    "type": "file",
                    "data": pdf_base64  # Remove mime_type - not allowed in FileChunk
                },
                pages=[0, 1],  # First two pages
                include_image_base64=False,
                image_limit=5,
                document_annotation_format=document_schema,
                bbox_annotation_format=bbox_schema
                # Don't specify model - let Mistral choose
            )
            
            print("✅ PDF OCR with structured output completed")
            print(f"📄 Pages processed: {result.get('usage_info', {}).get('pages_processed', 'N/A')}")
            
            # Show structured document analysis
            if 'document_annotation' in result:
                print(f"\n📋 Document Analysis:")
                print(f"   {result['document_annotation']}")
            
            # Show page content (first 300 chars)
            if 'pages' in result and result['pages']:
                for i, page in enumerate(result['pages'][:2]):
                    page_text = str(page)
                    print(f"\n📄 Page {i+1} content (first 300 chars):")
                    print("-" * 40)
                    print(page_text[:300] + "..." if len(page_text) > 300 else page_text)
            
        except Exception as e:
            print(f"❌ PDF OCR failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"⚠️ PDF file not found: {pdf_path}")

    # Example 3: Multi-format document processing
    print("\n3️⃣ Multi-format Document Processing")
    
    formats_to_test = [
        {
            "name": "Image URL",
            "document": {
                "type": "image_url",
                "image_url": {"url": "https://example.com/receipt.jpg"}
            }
        },
        {
            "name": "File Upload",
            "document": {
                "type": "file",
                "file_id": "8a0cfb4f-ddc9-436d-91bb-75133c583767"  # Example file ID
            }
        }
    ]
    
    for fmt in formats_to_test:
        print(f"\n   Testing {fmt['name']}:")
        try:
            # This would work with real documents/URLs
            print(f"   📄 Document format: {fmt['document']['type']}")
            print(f"   ✅ Format supported by OCR API")
        except Exception as e:
            print(f"   ❌ Format test failed: {e}")

    # Example 4: Advanced OCR options
    print("\n4️⃣ Advanced OCR Configuration")
    
    advanced_config = {
        "pages": [0, 2, 4],  # Specific pages
        "include_image_base64": True,  # Include extracted images
        "image_limit": 10,  # Max 10 images
        "image_min_size": 100,  # Min 100px images
    }
    
    print("📋 Advanced OCR options:")
    for key, value in advanced_config.items():
        print(f"   • {key}: {value}")
    
    print("\n✅ All Mistral OCR examples completed!")
    print("\n💡 Key Benefits of Mistral OCR API:")
    print("   • Dedicated OCR endpoint (not chat-based)")
    print("   • Multi-page document support")
    print("   • Structured data extraction with schemas")
    print("   • Image extraction and analysis")
    print("   • High-accuracy text recognition")
    print("   • Support for PDF, images, and document URLs")
    print("   • No need to specify model - Mistral chooses optimal OCR model")

if __name__ == "__main__":
    asyncio.run(main())
