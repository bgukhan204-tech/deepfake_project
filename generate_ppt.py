import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6] # Blank slide layout

    # Colors
    DARK_NAVY = RGBColor(11, 25, 44)       # #0B192C
    LIGHT_GRAY = RGBColor(245, 247, 250)   # #F5F7FA
    WHITE = RGBColor(255, 255, 255)
    DARK_SLATE = RGBColor(15, 23, 42)      # #0F172A
    TEAL = RGBColor(14, 116, 144)          # #0E7490 (for light slide categories)
    LIGHT_TEAL = RGBColor(56, 189, 248)    # #38BDF8 (for dark slide highlights)
    GRAY_TEXT = RGBColor(100, 116, 139)    # #64748B
    CARD_BG = RGBColor(255, 255, 255)      # White background for cards

    def add_solid_bg(slide, color):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = color

    def draw_left_accent_bar(slide):
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.4), Inches(7.5))
        shape.fill.solid()
        shape.fill.fore_color.rgb = LIGHT_TEAL
        shape.line.fill.background()

    def add_header(slide, title, category=None, is_dark=False):
        if category:
            cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.4))
            tf = cat_box.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            p.text = category.upper()
            p.font.name = 'Arial'
            p.font.size = Pt(11)
            p.font.bold = True
            p.font.color.rgb = LIGHT_TEAL if is_dark else TEAL

        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(11.7), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title
        p_title.font.name = 'Arial'
        p_title.font.size = Pt(28)
        p_title.font.bold = True
        p_title.font.color.rgb = WHITE if is_dark else DARK_SLATE

    def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=None):
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        if border_color:
            shape.line.color.rgb = border_color
            shape.line.width = Pt(1)
        else:
            shape.line.fill.background()
        return shape

    # ==========================================
    # SLIDE 1: Title Slide (Dark Theme)
    # ==========================================
    slide1 = prs.slides.add_slide(blank_layout)
    add_solid_bg(slide1, DARK_NAVY)
    draw_left_accent_bar(slide1)

    # Accent visual element (a large subtle square or box in background)
    bg_shape = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(8.5), Inches(0), Inches(4.833), Inches(7.5))
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = RGBColor(16, 32, 56)
    bg_shape.line.fill.background()

    # Title & Subtitle text frames
    title_box = slide1.shapes.add_textbox(Inches(1.2), Inches(2.2), Inches(11), Inches(3))
    tf = title_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    
    p = tf.paragraphs[0]
    p.text = "DEEPSHIELD"
    p.font.name = 'Arial'
    p.font.size = Pt(56)
    p.font.bold = True
    p.font.color.rgb = LIGHT_TEAL
    
    p2 = tf.add_paragraph()
    p2.text = "Multi-Engine AI Deepfake & Image Manipulation Detector"
    p2.font.name = 'Arial'
    p2.font.size = Pt(22)
    p2.font.color.rgb = WHITE
    p2.space_before = Pt(15)

    p3 = tf.add_paragraph()
    p3.text = "A hybrid forensic suite combining Deep Learning models, localized pixel JPEG compression checks, and texture noise analysis for state-of-the-art media validation."
    p3.font.name = 'Arial'
    p3.font.size = Pt(14)
    p3.font.color.rgb = RGBColor(148, 163, 184)
    p3.space_before = Pt(15)

    # Project metadata
    meta_box = slide1.shapes.add_textbox(Inches(1.2), Inches(5.8), Inches(6), Inches(1))
    tf_meta = meta_box.text_frame
    tf_meta.word_wrap = True
    tf_meta.margin_left = tf_meta.margin_top = tf_meta.margin_right = tf_meta.margin_bottom = 0
    pm = tf_meta.paragraphs[0]
    pm.text = "Technical Presentation  •  Deep Learning & Computer Vision"
    pm.font.name = 'Arial'
    pm.font.size = Pt(12)
    pm.font.color.rgb = LIGHT_TEAL
    pm.font.bold = True

    pm2 = tf_meta.add_paragraph()
    pm2.text = "Built with Python, TensorFlow, Flask, OpenCV & HTML5/CSS3/JS"
    pm2.font.name = 'Arial'
    pm2.font.size = Pt(11)
    pm2.font.color.rgb = RGBColor(100, 116, 139)
    pm2.space_before = Pt(5)

    # ==========================================
    # SLIDE 2: Project Overview & Objectives (Light Theme)
    # ==========================================
    slide2 = prs.slides.add_slide(blank_layout)
    add_solid_bg(slide2, LIGHT_GRAY)
    add_header(slide2, "The Proliferation of Synthesized Media", "Overview & Context")

    # Left Card: The Problem
    add_card(slide2, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    left_tb = slide2.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.0), Inches(4.2))
    ltf = left_tb.text_frame
    ltf.word_wrap = True
    ltf.margin_left = ltf.margin_top = ltf.margin_right = ltf.margin_bottom = 0
    
    lp1 = ltf.paragraphs[0]
    lp1.text = "THE DEEPFAKE CHALLENGE"
    lp1.font.name = 'Arial'
    lp1.font.size = Pt(14)
    lp1.font.bold = True
    lp1.font.color.rgb = TEAL

    bullets_left = [
        ("Hyper-Realistic AI Generation", "Advanced generative models (GANs, Diffusion, Face-Swap tools) produce synthetic images that are virtually indistinguishable from real photographs to the human eye."),
        ("Erosion of Digital Trust", "Manipulated media is heavily weaponized to spread misinformation, execute identity theft, run social engineering scams, and falsify digital evidence."),
        ("Traditional Limitations", "Relying on a single detection source (e.g., just a neural network) makes a system highly vulnerable to adversarial evasion and domain shifts.")
    ]
    for b_title, b_desc in bullets_left:
        p_title = ltf.add_paragraph()
        p_title.text = f"•  {b_title}"
        p_title.font.name = 'Arial'
        p_title.font.size = Pt(13)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_SLATE
        p_title.space_before = Pt(12)
        
        p_desc = ltf.add_paragraph()
        p_desc.text = b_desc
        p_desc.font.name = 'Arial'
        p_desc.font.size = Pt(11)
        p_desc.font.color.rgb = GRAY_TEXT
        p_desc.space_before = Pt(2)
        p_desc.margin_left = Inches(0.2)

    # Right Card: Project Objectives
    add_card(slide2, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    right_tb = slide2.shapes.add_textbox(Inches(7.1), Inches(2.1), Inches(5.1), Inches(4.2))
    rtf = right_tb.text_frame
    rtf.word_wrap = True
    rtf.margin_left = rtf.margin_top = rtf.margin_right = rtf.margin_bottom = 0
    
    rp1 = rtf.paragraphs[0]
    rp1.text = "PROJECT OBJECTIVES"
    rp1.font.name = 'Arial'
    rp1.font.size = Pt(14)
    rp1.font.bold = True
    rp1.font.color.rgb = TEAL

    bullets_right = [
        ("Multi-Modal Validation Suite", "Design a hybrid, 3-engine detection framework that evaluates image authenticity from physical, biological, and mathematical angles simultaneously."),
        ("Edge & Serverless Optimization", "Optimize complex deep learning models using quantization techniques to achieve rapid sub-100ms inference times on serverless infrastructure."),
        ("Forensic Transparency", "Provide the end-user with granular metrics (e.g., ELA maps, noise variance, prediction confidence) instead of simple, opaque binary flags.")
    ]
    for b_title, b_desc in bullets_right:
        p_title = rtf.add_paragraph()
        p_title.text = f"•  {b_title}"
        p_title.font.name = 'Arial'
        p_title.font.size = Pt(13)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_SLATE
        p_title.space_before = Pt(12)
        
        p_desc = rtf.add_paragraph()
        p_desc.text = b_desc
        p_desc.font.name = 'Arial'
        p_desc.font.size = Pt(11)
        p_desc.font.color.rgb = GRAY_TEXT
        p_desc.space_before = Pt(2)
        p_desc.margin_left = Inches(0.2)


    # ==========================================
    # SLIDE 3: System Architecture (Light Theme)
    # ==========================================
    slide3 = prs.slides.add_slide(blank_layout)
    add_solid_bg(slide3, LIGHT_GRAY)
    add_header(slide3, "Multi-Modal Ensemble Detection Framework", "System Design")

    # Draw 3 vertical cards
    card_width = Inches(3.68)
    card_height = Inches(4.6)
    card_y = Inches(2.0)
    gap = Inches(0.35)

    engines = [
        ("NEURAL ENGINE (DL)", "50% Core Weight", "Target: Biological Anomalies", 
         ["MobileNetV2 transfer learning backbone trained to detect deepfake anomalies.",
          "Haar Cascade face localization pipeline crops and scales facial regions.",
          "Identifies deep generative patterns and biological inconsistencies on face meshes."]),
        ("ERROR LEVEL ANALYSIS", "35% Core Weight", "Target: Compression Edits", 
         ["Heuristic algorithm analyzing compression discrepancies within pixels.",
          "Resaves images at 90% quality and computes absolute error mapping.",
          "Identifies local copy-pastes, digital modifications, and AI-inpaintings."]),
        ("TEXTURE & NOISE ENGINE", "15% Core Weight", "Target: GAN Smoothing", 
         ["High-frequency Laplacian filter capturing camera sensor noise patterns.",
          "Calculates image Laplacian variance to spot AI texture characteristics.",
          "Identifies artificial smoothing, blending borders, and software blur."])
    ]

    for idx, (title, weight, target, bullets) in enumerate(engines):
        left_pos = Inches(0.8) + idx * (card_width + gap)
        add_card(slide3, left_pos, card_y, card_width, card_height)
        
        tb = slide3.shapes.add_textbox(left_pos + Inches(0.25), card_y + Inches(0.3), card_width - Inches(0.5), card_height - Inches(0.6))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        # Category weight badge
        p_w = tf.paragraphs[0]
        p_w.text = f"{weight}  •  {target}"
        p_w.font.name = 'Arial'
        p_w.font.size = Pt(10)
        p_w.font.bold = True
        p_w.font.color.rgb = TEAL
        
        # Engine Title
        p_t = tf.add_paragraph()
        p_t.text = title
        p_t.font.name = 'Arial'
        p_t.font.size = Pt(18)
        p_t.font.bold = True
        p_t.font.color.rgb = DARK_SLATE
        p_t.space_before = Pt(8)
        p_t.space_after = Pt(15)

        # Bullet list
        for b in bullets:
            p_b = tf.add_paragraph()
            p_b.text = f"▪  {b}"
            p_b.font.name = 'Arial'
            p_b.font.size = Pt(11)
            p_b.font.color.rgb = GRAY_TEXT
            p_b.space_before = Pt(8)
            p_b.space_after = Pt(2)


    # ==========================================
    # SLIDE 4: Machine Learning Model (Light Theme)
    # ==========================================
    slide4 = prs.slides.add_slide(blank_layout)
    add_solid_bg(slide4, LIGHT_GRAY)
    add_header(slide4, "MobileNetV2 Transfer Learning Backbone", "Model Architecture")

    # Left Column: Base Model Choice
    add_card(slide4, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    left_tb = slide4.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.0), Inches(4.2))
    ltf = left_tb.text_frame
    ltf.word_wrap = True
    ltf.margin_left = ltf.margin_top = ltf.margin_right = ltf.margin_bottom = 0
    
    lp1 = ltf.paragraphs[0]
    lp1.text = "BASE MODEL & SELECTION RATIONALE"
    lp1.font.name = 'Arial'
    lp1.font.size = Pt(14)
    lp1.font.bold = True
    lp1.font.color.rgb = TEAL

    bullets_left = [
        ("Pre-trained MobileNetV2", "Uses weights pre-trained on ImageNet. MobileNetV2 is selected for its inverted residual blocks and linear bottlenecks, maintaining high expressiveness with small footprints."),
        ("Efficiency & Speed", "Features only 3.4M parameters compared to ResNet50 (25M+) or Xception (22M+). This dramatically reduces CPU inference latency, crucial for web hosting and serverless deployments."),
        ("Feature Extraction", "Freezing initial convolutional layers retains early visual feature filters (edges, textures) which are highly transferable to human facial structures.")
    ]
    for b_title, b_desc in bullets_left:
        p_title = ltf.add_paragraph()
        p_title.text = f"•  {b_title}"
        p_title.font.name = 'Arial'
        p_title.font.size = Pt(13)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_SLATE
        p_title.space_before = Pt(12)
        
        p_desc = ltf.add_paragraph()
        p_desc.text = b_desc
        p_desc.font.name = 'Arial'
        p_desc.font.size = Pt(11)
        p_desc.font.color.rgb = GRAY_TEXT
        p_desc.space_before = Pt(2)
        p_desc.margin_left = Inches(0.2)

    # Right Card: Custom Classification Head
    add_card(slide4, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    right_tb = slide4.shapes.add_textbox(Inches(7.1), Inches(2.1), Inches(5.1), Inches(4.2))
    rtf = right_tb.text_frame
    rtf.word_wrap = True
    rtf.margin_left = rtf.margin_top = rtf.margin_right = rtf.margin_bottom = 0
    
    rp1 = rtf.paragraphs[0]
    rp1.text = "CLASSIFICATION HEAD PIPELINE"
    rp1.font.name = 'Arial'
    rp1.font.size = Pt(14)
    rp1.font.bold = True
    rp1.font.color.rgb = TEAL

    bullets_right = [
        ("Input Dimension", "Accepts standard 224 × 224 × 3 RGB image inputs."),
        ("Global Average Pooling 2D", "Reduces the spatial size of the feature maps to a 1D vector (1280 features) by calculating the average of each channel, avoiding massive parameter bloat."),
        ("Dense Bottleneck Layer", "A fully connected layer with 128 units and ReLU activation maps features to a compact, discriminative latent representation."),
        ("Regularization (Dropout)", "30% Dropout (`rate=0.3`) applied during training to prevent co-adaptation of weights and combat dataset overfitting."),
        ("Binary output", "Single Dense unit with Sigmoid activation. Yields prediction in range [0.0, 1.0], where scores <= 0.5 denote Fake and > 0.5 denote Real.")
    ]
    for idx, (b_title, b_desc) in enumerate(bullets_right):
        p_title = rtf.add_paragraph()
        p_title.text = f"•  {b_title}"
        p_title.font.name = 'Arial'
        p_title.font.size = Pt(12)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_SLATE
        p_title.space_before = Pt(8 if idx > 0 else 12)
        
        p_desc = rtf.add_paragraph()
        p_desc.text = b_desc
        p_desc.font.name = 'Arial'
        p_desc.font.size = Pt(11)
        p_desc.font.color.rgb = GRAY_TEXT
        p_desc.space_before = Pt(2)
        p_desc.margin_left = Inches(0.2)


    # ==========================================
    # SLIDE 5: Training Pipeline & Optimization (Light Theme)
    # ==========================================
    slide5 = prs.slides.add_slide(blank_layout)
    add_solid_bg(slide5, LIGHT_GRAY)
    add_header(slide5, "Dual-Phase Training & Quantized TFLite Conversion", "Training & Optimization")

    # Left Column: Dual-Phase Fine-Tuning
    add_card(slide5, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    left_tb = slide5.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.0), Inches(4.2))
    ltf = left_tb.text_frame
    ltf.word_wrap = True
    ltf.margin_left = ltf.margin_top = ltf.margin_right = ltf.margin_bottom = 0
    
    lp1 = ltf.paragraphs[0]
    lp1.text = "TWO-PHASE TRAINING PROCEDURE"
    lp1.font.name = 'Arial'
    lp1.font.size = Pt(14)
    lp1.font.bold = True
    lp1.font.color.rgb = TEAL

    bullets_left = [
        ("Phase 1: Classifier Training", "Initial training with the MobileNetV2 base frozen (`trainable=False`). Focuses on optimizing the custom Dense classification layers. Settings: Adam optimizer with learning rate 1e-3, Binary Cross-Entropy loss, trained for 3 epochs."),
        ("Phase 2: Fine-Tuning Top Layers", "The base model is unfrozen, but the bottom 100 layers remain frozen to preserve foundational edge/texture filters. The top layers are fine-tuned with a lower learning rate of 1e-5 to prevent catastrophic forgetting. Trained for 3 epochs."),
        ("Data Augmentation", "ImageDataGenerator rescales images (1/255.0) and applies rotation (10 deg), horizontal flip, and width/height shifts (8%) to enhance generalization.")
    ]
    for b_title, b_desc in bullets_left:
        p_title = ltf.add_paragraph()
        p_title.text = f"•  {b_title}"
        p_title.font.name = 'Arial'
        p_title.font.size = Pt(13)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_SLATE
        p_title.space_before = Pt(12)
        
        p_desc = ltf.add_paragraph()
        p_desc.text = b_desc
        p_desc.font.name = 'Arial'
        p_desc.font.size = Pt(11)
        p_desc.font.color.rgb = GRAY_TEXT
        p_desc.space_before = Pt(2)
        p_desc.margin_left = Inches(0.2)

    # Right Card: Quantization & Deployment
    add_card(slide5, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    right_tb = slide5.shapes.add_textbox(Inches(7.1), Inches(2.1), Inches(5.1), Inches(4.2))
    rtf = right_tb.text_frame
    rtf.word_wrap = True
    rtf.margin_left = rtf.margin_top = rtf.margin_right = rtf.margin_bottom = 0
    
    rp1 = rtf.paragraphs[0]
    rp1.text = "TFLITE QUANTIZATION & DEPLOYMENT"
    rp1.font.name = 'Arial'
    rp1.font.size = Pt(14)
    rp1.font.bold = True
    rp1.font.color.rgb = TEAL

    bullets_right = [
        ("Optimized TFLite Conversion", "Converts the Keras H5 model (~90MB) to highly optimized TensorFlow Lite format. Applying `tf.lite.Optimize.DEFAULT` post-training quantization compresses weights from float32 to float16/int8."),
        ("Significant Resource Savings", "Reduces model file size by 75% down to only ~22MB. Allows for extremely fast, low-memory execution inside headless virtual environments and web runtimes."),
        ("In-Memory Loading Strategy", "Bypasses standard file system mapping (`mmap`) issues typical in cloud hosting servers (e.g. Render). Loads the model binary straight from memory (`model_content` buffer) to ensure 100% startup reliability.")
    ]
    for b_title, b_desc in bullets_right:
        p_title = rtf.add_paragraph()
        p_title.text = f"•  {b_title}"
        p_title.font.name = 'Arial'
        p_title.font.size = Pt(13)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_SLATE
        p_title.space_before = Pt(12)
        
        p_desc = rtf.add_paragraph()
        p_desc.text = b_desc
        p_desc.font.name = 'Arial'
        p_desc.font.size = Pt(11)
        p_desc.font.color.rgb = GRAY_TEXT
        p_desc.space_before = Pt(2)
        p_desc.margin_left = Inches(0.2)


    # ==========================================
    # SLIDE 6: Face Localization & Preprocessing (Light Theme)
    # ==========================================
    slide6 = prs.slides.add_slide(blank_layout)
    add_solid_bg(slide6, LIGHT_GRAY)
    add_header(slide6, "Robust Face Extraction & Normalization", "Neural Engine Preprocessing")

    # Left Column: Bounding Box
    add_card(slide6, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    left_tb = slide6.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.0), Inches(4.2))
    ltf = left_tb.text_frame
    ltf.word_wrap = True
    ltf.margin_left = ltf.margin_top = ltf.margin_right = ltf.margin_bottom = 0
    
    lp1 = ltf.paragraphs[0]
    lp1.text = "FACE LOCALIZATION ALGORITHM"
    lp1.font.name = 'Arial'
    lp1.font.size = Pt(14)
    lp1.font.bold = True
    lp1.font.color.rgb = TEAL

    bullets_left = [
        ("Haar Cascade Classifier", "Uses OpenCV's pre-trained frontal face cascade detector for fast and efficient region proposal."),
        ("Histogram Equalization", "Applies `cv2.equalizeHist` to gray frames to handle poor contrast and uneven lighting. If equalization fails, falls back to raw grayscale to maximize detection probability."),
        ("Largest Face Selection", "Sorts detected faces by area (`width * height`) and selects the largest face to ignore background spectators.")
    ]
    for b_title, b_desc in bullets_left:
        p_title = ltf.add_paragraph()
        p_title.text = f"•  {b_title}"
        p_title.font.name = 'Arial'
        p_title.font.size = Pt(13)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_SLATE
        p_title.space_before = Pt(12)
        
        p_desc = ltf.add_paragraph()
        p_desc.text = b_desc
        p_desc.font.name = 'Arial'
        p_desc.font.size = Pt(11)
        p_desc.font.color.rgb = GRAY_TEXT
        p_desc.space_before = Pt(2)
        p_desc.margin_left = Inches(0.2)

    # Right Card: Normalization & Fallback
    add_card(slide6, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    right_tb = slide6.shapes.add_textbox(Inches(7.1), Inches(2.1), Inches(5.1), Inches(4.2))
    rtf = right_tb.text_frame
    rtf.word_wrap = True
    rtf.margin_left = rtf.margin_top = rtf.margin_right = rtf.margin_bottom = 0
    
    rp1 = rtf.paragraphs[0]
    rp1.text = "NORMALIZATION & FALLBACK RULES"
    rp1.font.name = 'Arial'
    rp1.font.size = Pt(14)
    rp1.font.bold = True
    rp1.font.color.rgb = TEAL

    bullets_right = [
        ("1.4x Padding Margin", "Expands the raw bounding box width and height by 40% to include crucial facial boundary regions (cheeks, ears, hairline) where artifacts frequently accumulate."),
        ("1:1 Aspect Ratio Crop", "Forces crops into perfect squares. Prevents spatial distortion and stretching when resizing the image to the neural network's strict dimensions."),
        ("Zero-Stretch Fallback", "If no faces are detected in the frame, it automatically extracts a 1:1 center-square crop of the original photo. Avoids squishing rectangular images, which introduces synthetic artifacts.")
    ]
    for b_title, b_desc in bullets_right:
        p_title = rtf.add_paragraph()
        p_title.text = f"•  {b_title}"
        p_title.font.name = 'Arial'
        p_title.font.size = Pt(13)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_SLATE
        p_title.space_before = Pt(12)
        
        p_desc = rtf.add_paragraph()
        p_desc.text = b_desc
        p_desc.font.name = 'Arial'
        p_desc.font.size = Pt(11)
        p_desc.font.color.rgb = GRAY_TEXT
        p_desc.space_before = Pt(2)
        p_desc.margin_left = Inches(0.2)


    # ==========================================
    # SLIDE 7: Error Level Analysis (ELA) Engine (Light Theme)
    # ==========================================
    slide7 = prs.slides.add_slide(blank_layout)
    add_solid_bg(slide7, LIGHT_GRAY)
    add_header(slide7, "Quantizing Inconsistent Image Compression", "Error Level Analysis (ELA) Engine")

    # Left Column: How ELA Works
    add_card(slide7, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    left_tb = slide7.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.0), Inches(4.2))
    ltf = left_tb.text_frame
    ltf.word_wrap = True
    ltf.margin_left = ltf.margin_top = ltf.margin_right = ltf.margin_bottom = 0
    
    lp1 = ltf.paragraphs[0]
    lp1.text = "THE ELA METHODOLOGY"
    lp1.font.name = 'Arial'
    lp1.font.size = Pt(14)
    lp1.font.bold = True
    lp1.font.color.rgb = TEAL

    bullets_left = [
        ("Re-Compression Principle", "The engine saves the input image in memory at a specific JPEG quality (90%). It then computes the absolute difference between the original pixel values and the newly compressed pixel values."),
        ("JPEG Compression Behavior", "In authentic images, the error is uniform across the entire image grid. Pixels compress and discard details at a uniform rate, showing low baseline differences."),
        ("Detecting Local Splices", "If a section is edited or AI-synthesized (e.g. face-swapped), its pixels possess different compression history. When re-compressed, it creates higher error variance, highlighting manipulated boundaries.")
    ]
    for b_title, b_desc in bullets_left:
        p_title = ltf.add_paragraph()
        p_title.text = f"•  {b_title}"
        p_title.font.name = 'Arial'
        p_title.font.size = Pt(13)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_SLATE
        p_title.space_before = Pt(12)
        
        p_desc = ltf.add_paragraph()
        p_desc.text = b_desc
        p_desc.font.name = 'Arial'
        p_desc.font.size = Pt(11)
        p_desc.font.color.rgb = GRAY_TEXT
        p_desc.space_before = Pt(2)
        p_desc.margin_left = Inches(0.2)

    # Right Card: Interpretation & Scoring
    add_card(slide7, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    right_tb = slide7.shapes.add_textbox(Inches(7.1), Inches(2.1), Inches(5.1), Inches(4.2))
    rtf = right_tb.text_frame
    rtf.word_wrap = True
    rtf.margin_left = rtf.margin_top = rtf.margin_right = rtf.margin_bottom = 0
    
    rp1 = rtf.paragraphs[0]
    rp1.text = "SCORING & CALIBRATION METRICS"
    rp1.font.name = 'Arial'
    rp1.font.size = Pt(14)
    rp1.font.bold = True
    rp1.font.color.rgb = TEAL

    bullets_right = [
        ("Mean Absolute Error (MAE)", "Measures average difference per pixel. Real images average 1.0 to 5.0 in MAE. AI face swaps and local edits often average 6.0 to 20.0+ MAE."),
        ("Calibrated Manipulation Score", "The MAE is mapped to a 0% - 100% score: `manipulation_score = min(100.0, (mean_diff / 18.0) * 100)`."),
        ("Forensic Artifact Detection", "Effectively isolates local copy-paste splices, digital airbrush edits, and boundary blend artifacts generated by generative adversarial networks (GANs).")
    ]
    for b_title, b_desc in bullets_right:
        p_title = rtf.add_paragraph()
        p_title.text = f"•  {b_title}"
        p_title.font.name = 'Arial'
        p_title.font.size = Pt(13)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_SLATE
        p_title.space_before = Pt(12)
        
        p_desc = rtf.add_paragraph()
        p_desc.text = b_desc
        p_desc.font.name = 'Arial'
        p_desc.font.size = Pt(11)
        p_desc.font.color.rgb = GRAY_TEXT
        p_desc.space_before = Pt(2)
        p_desc.margin_left = Inches(0.2)


    # ==========================================
    # SLIDE 8: Texture & Noise Analysis Engine (Light Theme)
    # ==========================================
    slide8 = prs.slides.add_slide(blank_layout)
    add_solid_bg(slide8, LIGHT_GRAY)
    add_header(slide8, "Laplacian Variance for High-Frequency Noise", "Texture & Noise Analysis Engine")

    # Left Column: Texture & Blur Analysis
    add_card(slide8, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    left_tb = slide8.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.0), Inches(4.2))
    ltf = left_tb.text_frame
    ltf.word_wrap = True
    ltf.margin_left = ltf.margin_top = ltf.margin_right = ltf.margin_bottom = 0
    
    lp1 = ltf.paragraphs[0]
    lp1.text = "HIGH-FREQUENCY SENSOR NOISE"
    lp1.font.name = 'Arial'
    lp1.font.size = Pt(14)
    lp1.font.bold = True
    lp1.font.color.rgb = TEAL

    bullets_left = [
        ("Sensor Noise Characteristics", "Authentic digital cameras capture raw physical sensor noise (high-frequency grain). This pattern exists uniformly across natural, unaltered regions."),
        ("AI Over-Smoothing Signature", "Generative adversarial networks (GANs) and neural generators struggle to reproduce consistent, micro-level sensor noise. Instead, they produce smoothed pixels and blending gradients."),
        ("Detection Vector", "Focuses on identifying digital airbrushing, artificial softening, and the loss of edge detail common in deepfake blending borders.")
    ]
    for b_title, b_desc in bullets_left:
        p_title = ltf.add_paragraph()
        p_title.text = f"•  {b_title}"
        p_title.font.name = 'Arial'
        p_title.font.size = Pt(13)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_SLATE
        p_title.space_before = Pt(12)
        
        p_desc = ltf.add_paragraph()
        p_desc.text = b_desc
        p_desc.font.name = 'Arial'
        p_desc.font.size = Pt(11)
        p_desc.font.color.rgb = GRAY_TEXT
        p_desc.space_before = Pt(2)
        p_desc.margin_left = Inches(0.2)

    # Right Card: Laplacian Variance Classifier
    add_card(slide8, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    right_tb = slide8.shapes.add_textbox(Inches(7.1), Inches(2.1), Inches(5.1), Inches(4.2))
    rtf = right_tb.text_frame
    rtf.word_wrap = True
    rtf.margin_left = rtf.margin_top = rtf.margin_right = rtf.margin_bottom = 0
    
    rp1 = rtf.paragraphs[0]
    rp1.text = "LAPLACIAN VARIANCE STRATEGY"
    rp1.font.name = 'Arial'
    rp1.font.size = Pt(14)
    rp1.font.bold = True
    rp1.font.color.rgb = TEAL

    bullets_right = [
        ("Laplacian Filter Application", "Applies an isotropic OpenCV Laplacian convolution kernel to the grayscale image. Evaluates the standard variance of the filtered matrix."),
        ("Variance > 70 (Authentic)", "Indicates healthy high-frequency details, sharp edges, and normal camera sensor noise patterns. Expected in unedited photography."),
        ("Variance < 35 (Manipulated)", "Denotes extreme lack of high-frequency noise. Spots over-smoothing, soft gradients, and synthetic texture fields. Calibrates an artificial smoothing score: `smoothing_score = min(100.0, (35.0 - lap_var) * 2.5)`.")
    ]
    for b_title, b_desc in bullets_right:
        p_title = rtf.add_paragraph()
        p_title.text = f"•  {b_title}"
        p_title.font.name = 'Arial'
        p_title.font.size = Pt(13)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_SLATE
        p_title.space_before = Pt(12)
        
        p_desc = rtf.add_paragraph()
        p_desc.text = b_desc
        p_desc.font.name = 'Arial'
        p_desc.font.size = Pt(11)
        p_desc.font.color.rgb = GRAY_TEXT
        p_desc.space_before = Pt(2)
        p_desc.margin_left = Inches(0.2)


    # ==========================================
    # SLIDE 9: Dashboard & Web Application (Light Theme)
    # ==========================================
    slide9 = prs.slides.add_slide(blank_layout)
    add_solid_bg(slide9, LIGHT_GRAY)
    add_header(slide9, "Flask-Powered Modern Forensic Dashboard", "Dashboard & User Interface")

    # Left Column: User Interface Highlights
    add_card(slide9, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    left_tb = slide9.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.0), Inches(4.2))
    ltf = left_tb.text_frame
    ltf.word_wrap = True
    ltf.margin_left = ltf.margin_top = ltf.margin_right = ltf.margin_bottom = 0
    
    lp1 = ltf.paragraphs[0]
    lp1.text = "DEEPSHIELD FRONT-END SUITE"
    lp1.font.name = 'Arial'
    lp1.font.size = Pt(14)
    lp1.font.bold = True
    lp1.font.color.rgb = TEAL

    bullets_left = [
        ("Interactive Forensic Dashboard", "Features a clean, modern, dark-themed responsive dashboard interface using vanilla CSS variables, glassmorphism, and responsive CSS grids."),
        ("Multi-Modal Media Capture", "Supports drag-and-drop file upload, file selector, and real-time webcam frame acquisition using Javascript API (`MediaDevices.getUserMedia`)."),
        ("Live Calibration Graphing", "Plots real-time confidence radial bar charts, raw scores, Laplacian variance details, and ELA metrics to provide transparent detection feedback.")
    ]
    for b_title, b_desc in bullets_left:
        p_title = ltf.add_paragraph()
        p_title.text = f"•  {b_title}"
        p_title.font.name = 'Arial'
        p_title.font.size = Pt(13)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_SLATE
        p_title.space_before = Pt(12)
        
        p_desc = ltf.add_paragraph()
        p_desc.text = b_desc
        p_desc.font.name = 'Arial'
        p_desc.font.size = Pt(11)
        p_desc.font.color.rgb = GRAY_TEXT
        p_desc.space_before = Pt(2)
        p_desc.margin_left = Inches(0.2)

    # Right Card: Video Analysis Framework
    add_card(slide9, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    right_tb = slide9.shapes.add_textbox(Inches(7.1), Inches(2.1), Inches(5.1), Inches(4.2))
    rtf = right_tb.text_frame
    rtf.word_wrap = True
    rtf.margin_left = rtf.margin_top = rtf.margin_right = rtf.margin_bottom = 0
    
    rp1 = rtf.paragraphs[0]
    rp1.text = "VIDEO ANALYSIS FRAMEWORK"
    rp1.font.name = 'Arial'
    rp1.font.size = Pt(14)
    rp1.font.bold = True
    rp1.font.color.rgb = TEAL

    bullets_right = [
        ("Dynamic Frame Sampling", "Supports uploading `.mp4`, `.avi`, `.mov`, `.webm`. Uniformly extracts up to 12 frames across the entire video length, ensuring detection coverage without freezing system memory."),
        ("Ensemble Frame Validation", "Applies the ELA engine and TFLite Deep Learning model to every sample. Computes frame-level metrics and stores timestamps."),
        ("Interactive Timeline Graphing", "Builds a chronological timeline on the UI, showing the fluctuation of deepfake scores and compression errors across video progression.")
    ]
    for b_title, b_desc in bullets_right:
        p_title = rtf.add_paragraph()
        p_title.text = f"•  {b_title}"
        p_title.font.name = 'Arial'
        p_title.font.size = Pt(13)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_SLATE
        p_title.space_before = Pt(12)
        
        p_desc = rtf.add_paragraph()
        p_desc.text = b_desc
        p_desc.font.name = 'Arial'
        p_desc.font.size = Pt(11)
        p_desc.font.color.rgb = GRAY_TEXT
        p_desc.space_before = Pt(2)
        p_desc.margin_left = Inches(0.2)


    # ==========================================
    # SLIDE 10: Conclusion & Future Directions (Dark Theme)
    # ==========================================
    slide10 = prs.slides.add_slide(blank_layout)
    add_solid_bg(slide10, DARK_NAVY)
    draw_left_accent_bar(slide10)

    # Accent visual element
    bg_shape = slide10.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(8.5), Inches(0), Inches(4.833), Inches(7.5))
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = RGBColor(16, 32, 56)
    bg_shape.line.fill.background()

    add_header(slide10, "Empowering Digital Trust & Forensic Integrity", "Summary & Future Scope", is_dark=True)

    # Content Box
    content_box = slide10.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(7.2), Inches(4.8))
    tf_c = content_box.text_frame
    tf_c.word_wrap = True
    tf_c.margin_left = tf_c.margin_top = tf_c.margin_right = tf_c.margin_bottom = 0

    p_str = tf_c.paragraphs[0]
    p_str.text = "CORE STRENGTHS"
    p_str.font.name = 'Arial'
    p_str.font.size = Pt(14)
    p_str.font.bold = True
    p_str.font.color.rgb = LIGHT_TEAL

    strengths = [
        "Dual-Layer Forensic Security: Combines biological (DL face validation) and mathematical (ELA compression + texture noise variance) checks to neutralize adversarial evasion.",
        "Serverless Optimization: The quantized ~22MB TFLite model runs seamlessly with sub-100ms prediction speeds on standard CPUs.",
        "Interactive Transparency: Moves away from opaque binary labels, delivering detailed error heatmaps and clear reasoning."
    ]
    for s in strengths:
        title, desc = s.split(":")
        ps_t = tf_c.add_paragraph()
        ps_t.text = f"✔  {title}:"
        ps_t.font.name = 'Arial'
        ps_t.font.size = Pt(12)
        ps_t.font.bold = True
        ps_t.font.color.rgb = WHITE
        ps_t.space_before = Pt(8)
        
        ps_d = tf_c.add_paragraph()
        ps_d.text = desc.strip()
        ps_d.font.name = 'Arial'
        ps_d.font.size = Pt(11)
        ps_d.font.color.rgb = RGBColor(148, 163, 184)
        ps_d.space_before = Pt(2)
        ps_d.margin_left = Inches(0.2)

    # Future scope on right side (dark grey box)
    add_card(slide10, Inches(8.8), Inches(1.8), Inches(3.7), Inches(4.8), bg_color=RGBColor(24, 37, 56))
    f_box = slide10.shapes.add_textbox(Inches(9.05), Inches(2.1), Inches(3.2), Inches(4.2))
    tf_f = f_box.text_frame
    tf_f.word_wrap = True
    tf_f.margin_left = tf_f.margin_top = tf_f.margin_right = tf_f.margin_bottom = 0

    p_f = tf_f.paragraphs[0]
    p_f.text = "FUTURE ROADMAP"
    p_f.font.name = 'Arial'
    p_f.font.size = Pt(14)
    p_f.font.bold = True
    p_f.font.color.rgb = LIGHT_TEAL

    roadmap = [
        ("Audio Spoofing Detection", "Integrate voice cloning and synthetic audio spoofing verification checks for video inputs."),
        ("Vision Transformers (ViT)", "Explore ViT architectures to capture spatial self-attention artifacts and blending patch boundaries."),
        ("Live Stream Parsing", "Incorporate live RTMP stream connection and verification for real-time video broadcast inspection.")
    ]
    for idx, (title, desc) in enumerate(roadmap):
        pf_t = tf_f.add_paragraph()
        pf_t.text = f"{idx+1}. {title}"
        pf_t.font.name = 'Arial'
        pf_t.font.size = Pt(12)
        pf_t.font.bold = True
        pf_t.font.color.rgb = WHITE
        pf_t.space_before = Pt(12)
        
        pf_d = tf_f.add_paragraph()
        pf_d.text = desc
        pf_d.font.name = 'Arial'
        pf_d.font.size = Pt(11)
        pf_d.font.color.rgb = RGBColor(148, 163, 184)
        pf_d.space_before = Pt(2)
        pf_d.margin_left = Inches(0.15)


    # Save presentation
    output_filename = "Deepfake_Detection_Project_Presentation.pptx"
    prs.save(output_filename)
    print(f"Presentation successfully created: {output_filename}")

if __name__ == "__main__":
    create_presentation()
