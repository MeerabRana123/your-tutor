"""Script to generate a synthetic, multi-page machine learning test PDF fixture.

Explicitly labeled as synthetic educational test data, not an external textbook.
Used for deterministic testing of page-aware extraction, retrieval, and grounding.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak


def generate_synthetic_ml_pdf(output_path: Path) -> Path:
    """Generates a 4-page test PDF fixture covering core ML concepts."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "FixtureTitle",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "FixtureHeading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "FixtureBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        spaceAfter=10,
    )
    disclaimer_style = ParagraphStyle(
        "FixtureDisclaimer",
        parent=styles["Italic"],
        fontSize=8,
        leading=10,
        textColor="#555555",
        spaceAfter=14,
    )

    story = []

    # -------------------------------------------------------------------------
    # PAGE 1: Loss and Cost Functions
    # -------------------------------------------------------------------------
    story.append(Paragraph("SYNTHETIC TEST FIXTURE — MACHINE LEARNING FOUNDATIONS", title_style))
    story.append(Paragraph("DISCLAIMER: Synthetic test data generated exclusively for unit testing Your Tutor. Not an authentic published source.", disclaimer_style))
    story.append(Paragraph("Chapter 1: Loss and Cost Functions in Neural Networks", heading_style))
    story.append(Paragraph(
        "In supervised learning, loss functions measure the discrepancy between the model prediction and the true ground-truth target. "
        "A loss function evaluates an individual training example, whereas a cost function computes the average loss across the entire training dataset.",
        body_style,
    ))
    story.append(Paragraph(
        "For continuous regression problems, the standard formulation is Mean Squared Error (MSE), which squares the Euclidean residuals. "
        "For classification problems, Cross-Entropy Loss measures the information-theoretic divergence between the predicted probability distribution and true one-hot target classes.",
        body_style,
    ))
    story.append(Paragraph(
        "Empirical risk minimization seeks model parameters that minimize the aggregate cost function across observed samples. "
        "The curvature of the cost surface determines the difficulty of optimization and dictates the gradient landscape.",
        body_style,
    ))
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # PAGE 2: Gradient Descent Optimization
    # -------------------------------------------------------------------------
    story.append(Paragraph("SYNTHETIC TEST FIXTURE — MACHINE LEARNING FOUNDATIONS", title_style))
    story.append(Paragraph("DISCLAIMER: Synthetic test data generated exclusively for unit testing Your Tutor.", disclaimer_style))
    story.append(Paragraph("Chapter 2: Gradient Descent Optimization", heading_style))
    story.append(Paragraph(
        "Gradient descent is a first-order iterative optimization algorithm used to locate local minima of a differentiable cost function. "
        "At each iteration, parameters are updated in the direction of steepest descent, defined by the negative gradient of the objective function.",
        body_style,
    ))
    story.append(Paragraph(
        "The standard parameter update equation is: theta_new = theta_old - alpha * grad_J(theta), where alpha represents the learning rate hyperparameter. "
        "Selecting an appropriate learning rate is crucial: an excessively small learning rate causes painfully slow convergence, while an excessively large learning rate causes oscillations and divergence.",
        body_style,
    ))
    story.append(Paragraph(
        "There are three primary variants of gradient descent: Batch Gradient Descent evaluates the full training dataset per step; "
        "Stochastic Gradient Descent (SGD) updates parameters after each individual example, introducing stochastic noise that helps escape saddle points; "
        "and Mini-batch Gradient Descent calculates gradients over small batches (e.g., 32 to 256 samples), balancing vectorization speed with stochasticity.",
        body_style,
    ))
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # PAGE 3: Backpropagation and Computation Graphs
    # -------------------------------------------------------------------------
    story.append(Paragraph("SYNTHETIC TEST FIXTURE — MACHINE LEARNING FOUNDATIONS", title_style))
    story.append(Paragraph("DISCLAIMER: Synthetic test data generated exclusively for unit testing Your Tutor.", disclaimer_style))
    story.append(Paragraph("Chapter 3: Backpropagation and the Chain Rule", heading_style))
    story.append(Paragraph(
        "Backpropagation is the computational backbone of deep neural network training. It implements reverse-mode automatic differentiation over a directed computation graph. "
        "The fundamental mathematical principle underlying backpropagation is the multivariate chain rule of differential calculus.",
        body_style,
    ))
    story.append(Paragraph(
        "Training proceeds in two distinct phases: First, during the forward pass, input activations propagate through successive hidden layers to produce the network output and scalar loss. "
        "Second, during the backward pass, partial derivatives of the loss with respect to intermediate activations are computed recursively from the output layer backward toward the input layer.",
        body_style,
    ))
    story.append(Paragraph(
        "Specifically, for weight w connecting layer l-1 to layer l, the gradient is given by dL/dw = (dL/dz) * a^(l-1), where z is the linear pre-activation. "
        "Accumulating these layer-wise gradients allows gradient descent optimizers to adjust synaptic weights across multi-layer perceptrons.",
        body_style,
    ))
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # PAGE 4: Overfitting and Regularization Techniques
    # -------------------------------------------------------------------------
    story.append(Paragraph("SYNTHETIC TEST FIXTURE — MACHINE LEARNING FOUNDATIONS", title_style))
    story.append(Paragraph("DISCLAIMER: Synthetic test data generated exclusively for unit testing Your Tutor.", disclaimer_style))
    story.append(Paragraph("Chapter 4: Overfitting and Regularization Techniques", heading_style))
    story.append(Paragraph(
        "Overfitting is a central pathology in machine learning where a model achieves near-zero training error by memorizing noise and idiosyncrasies in the training sample, "
        "leading to high generalization error on unseen validation or test distributions. This exemplifies the classic high variance regime of the bias-variance tradeoff.",
        body_style,
    ))
    story.append(Paragraph(
        "To mitigate overfitting, regularization techniques constrain model complexity. "
        "L2 Regularization (also known as weight decay or ridge penalty) adds the sum of squared weights to the objective function, penalizing excessively large parameter magnitudes. "
        "L1 Regularization (lasso penalty) adds the sum of absolute values, encouraging sparsity by driving irrelevant weights to exact zeros.",
        body_style,
    ))
    story.append(Paragraph(
        "Another effective technique in deep learning is Dropout, introduced by Srivastava et al., which randomly deactivates a fraction p of hidden units during each forward training step. "
        "Dropout prevents co-adaptation of features and acts as an ensemble of thinned subnetworks. Early stopping monitors validation loss and halts training before overfitting occurs.",
        body_style,
    ))

    doc.build(story)
    return output_path


if __name__ == "__main__":
    out = Path("tests/fixtures/synthetic_ml_notes.pdf")
    generate_synthetic_ml_pdf(out)
    print(f"Generated synthetic ML PDF fixture at: {out.resolve()}")
