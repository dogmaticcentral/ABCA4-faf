# BRISQUE Algorithm

## What it Scores

BRISQUE (Blind/Referenceless Image Spatial Quality Evaluator) scores **image quality and sharpness** without needing a reference image to compare against. It detects:

- **Blur** and loss of sharpness
- **Noise** and artifacts
- **Distortions** and compression artifacts
- **Overall perceptual quality**

**Scoring range:** Typically 0-100, where:
- **Lower scores** = Better quality
- **Higher scores** = Worse quality

## How it Works

1. **No-Reference Assessment**: Unlike some quality metrics, BRISQUE doesn't need a pristine "reference" image to compare against—it assesses the image independently.

2. **Natural Scene Statistics (NSS)**: 
   - Analyzes the statistical properties of natural images
   - Extracts features from image gradients and local patterns
   - Measures deviations from what a "natural" image should look like

3. **Feature Extraction**:
   - Computes local mean and variance
   - Analyzes gradient magnitudes
   - Extracts spatial statistics from image patches

4. **Machine Learning Model**:
   - Uses a Support Vector Machine (SVM) trained on thousands of distorted images
   - The model learned to correlate statistical features with human perception of quality
   - Outputs a final quality score

## Key Advantages
- Fast computation
- No reference image needed
- Correlates well with human perception of image quality
- Works across different distortion types

# Quick stats calculation

```bash
grep -v 4000 all_tiffinfo.tsv | cut -f 5  | ministat -w 70
cut -f 5 controls_tiffinfo.tsv | ministat -w 70
```