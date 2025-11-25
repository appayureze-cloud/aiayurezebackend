#!/bin/bash

echo "🔍 Verifying HuggingFace Space Package..."
echo ""

# Check all required files
files=(
    "Dockerfile"
    "main_enhanced.py"
    "requirements.txt"
    "README.md"
    "SECRETS_LIST.txt"
)

all_good=true

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file - MISSING!"
        all_good=false
    fi
done

# Check app folder
if [ -d "app" ]; then
    echo "✅ app/ folder"
    echo "   Contains: $(ls -1 app | wc -l) files"
else
    echo "❌ app/ folder - MISSING!"
    all_good=false
fi

# Check static folder
if [ -d "static" ]; then
    echo "✅ static/ folder (empty, as expected)"
else
    echo "❌ static/ folder - MISSING!"
    all_good=false
fi

echo ""
if [ "$all_good" = true ]; then
    echo "✅ All files present! Ready to upload to HuggingFace Space!"
    echo ""
    echo "📦 Package contents:"
    echo "   - Dockerfile (GPU-optimized for T4)"
    echo "   - main_enhanced.py (Complete backend)"
    echo "   - requirements.txt (All dependencies)"
    echo "   - app/ (All modules)"
    echo "   - static/ (Required empty folder)"
    echo "   - README.md (Deployment guide)"
    echo "   - SECRETS_LIST.txt (List of secrets to add)"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Download this entire 'hf_space_deploy' folder"
    echo "   2. Go to https://huggingface.co/new-space"
    echo "   3. Create new Space with Docker SDK + T4 GPU"
    echo "   4. Upload all files from this folder"
    echo "   5. Add secrets (see SECRETS_LIST.txt)"
    echo "   6. Wait for build"
    echo "   7. Update WhatsApp webhook"
    echo "   8. Test!"
else
    echo "❌ Some files are missing! Please check above."
fi
