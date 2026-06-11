# IR Schema Definition

The Intermediate Representation (IR) is a structured JSON object that captures all implementation-relevant information from a research paper. All code generation phases work from the IR, not raw paper text.

## Schema

```json
{
  "paper": {
    "title": "string — paper title",
    "year": "number — publication year",
    "key_contributions": ["string — list of main contributions"]
  },
  "task": "string — task type: image_classification | object_detection | semantic_segmentation | sequence_to_sequence | text_classification | generation | reinforcement_learning | other",
  "framework": "string — pytorch | tensorflow",
  "components": {
    "model": {
      "name": "string — model name",
      "submodules": [
        {
          "name": "string — class name",
          "type": "string — layer type: conv | linear | attention | rnn | lstm | gru | embedding | normalization | activation | dropout | pooling | encoder | decoder | other",
          "params": {"key": "value — type-specific parameters"},
          "layers": "number — optional, number of repeated layers (e.g., Transformer has 6 encoder layers)",
          "connections": ["string — list of submodule names this connects to"]
        }
      ],
      "loss": "string — loss function: cross_entropy | mse | bce | ctc | contrastive | custom",
      "input_shape": "string — e.g., [batch, channels, height, width]",
      "output_shape": "string — e.g., [batch, num_classes]"
    },
    "data": {
      "dataset": "string — dataset name",
      "num_classes": "number — optional, for classification tasks",
      "vocab_size": "number — optional, for NLP tasks",
      "preprocess": ["string — preprocessing steps: normalize | resize | augment | tokenize | pad | mask"],
      "dataloader": {
        "batch_size": "number",
        "shuffle": "boolean",
        "num_workers": "number"
      }
    },
    "training": {
      "optimizer": "string — adam | sgd | adamw | rmsprop",
      "lr": "number — learning rate",
      "lr_schedule": "string — none | step | cosine | warmup_cosine | warmup_linear",
      "weight_decay": "number",
      "epochs": "number",
      "gradient_clip": "number — optional, max gradient norm",
      "mixed_precision": "boolean",
      "batch_size": "number"
    },
    "evaluation": {
      "metrics": ["string — accuracy | loss | bleu | rouge | f1 | precision | recall | iou | psnr | fid"],
      "test_loop": "boolean — whether a separate evaluation loop is needed"
    }
  },
  "files": {
    "filename.py": ["list of class/function names to include in this file"]
  },
  "dependencies": ["string — required pip packages beyond the framework"]
}
```

## Example: Transformer (Attention Is All You Need)

```json
{
  "paper": {
    "title": "Attention Is All You Need",
    "year": 2017,
    "key_contributions": ["self-attention mechanism", "Transformer architecture", "multi-head attention"]
  },
  "task": "sequence_to_sequence",
  "framework": "pytorch",
  "components": {
    "model": {
      "name": "Transformer",
      "submodules": [
        {"name": "MultiHeadAttention", "type": "attention", "params": {"d_model": 512, "n_heads": 8, "dropout": 0.1}, "connections": ["PositionalEncoding", "FeedForward"]},
        {"name": "PositionalEncoding", "type": "embedding", "params": {"d_model": 512, "max_len": 5000}, "connections": ["TransformerEncoder", "TransformerDecoder"]},
        {"name": "FeedForward", "type": "linear", "params": {"d_model": 512, "d_ff": 2048}, "connections": ["MultiHeadAttention"]},
        {"name": "TransformerEncoder", "type": "encoder", "layers": 6, "connections": ["MultiHeadAttention", "FeedForward"]},
        {"name": "TransformerDecoder", "type": "decoder", "layers": 6, "connections": ["MultiHeadAttention", "FeedForward", "TransformerEncoder"]}
      ],
      "loss": "cross_entropy",
      "input_shape": "[batch, src_seq_len] and [batch, tgt_seq_len]",
      "output_shape": "[batch, tgt_seq_len, vocab_size]"
    },
    "data": {
      "dataset": "WMT14",
      "vocab_size": 32000,
      "preprocess": ["tokenize", "pad", "mask"],
      "dataloader": {"batch_size": 32, "shuffle": true, "num_workers": 4}
    },
    "training": {
      "optimizer": "adam",
      "lr": 0.0001,
      "lr_schedule": "warmup_cosine",
      "weight_decay": 0.0,
      "epochs": 100,
      "gradient_clip": 1.0,
      "mixed_precision": false,
      "batch_size": 32
    },
    "evaluation": {
      "metrics": ["bleu", "loss"],
      "test_loop": true
    }
  },
  "files": {
    "model.py": ["MultiHeadAttention", "PositionalEncoding", "FeedForward", "TransformerEncoderLayer", "TransformerDecoderLayer", "Transformer"],
    "dataset.py": ["WMT14Dataset", "collate_fn"],
    "train.py": ["train_epoch", "train"],
    "evaluate.py": ["evaluate", "compute_bleu"],
    "utils.py": ["generate_padding_mask", "generate_causal_mask", "WarmupScheduler"]
  },
  "dependencies": ["torchtext", "sacrebleu"]
}
```

## Example: ResNet (Image Classification)

```json
{
  "paper": {
    "title": "Deep Residual Learning for Image Recognition",
    "year": 2015,
    "key_contributions": ["residual connections", "batch normalization", "deep network training"]
  },
  "task": "image_classification",
  "framework": "pytorch",
  "components": {
    "model": {
      "name": "ResNet",
      "submodules": [
        {"name": "ConvBlock", "type": "conv", "params": {"in_channels": 3, "out_channels": 64, "kernel_size": 7, "stride": 2}, "connections": ["MaxPool", "ResidualBlock"]},
        {"name": "ResidualBlock", "type": "conv", "params": {"channels": [64, 64, 256]}, "layers": 3, "connections": ["ConvBlock"]},
        {"name": "BottleneckBlock", "type": "conv", "params": {"reduction": 4}, "connections": ["ResidualBlock"]}
      ],
      "loss": "cross_entropy",
      "input_shape": "[batch, 3, 224, 224]",
      "output_shape": "[batch, num_classes]"
    },
    "data": {
      "dataset": "ImageNet",
      "num_classes": 1000,
      "preprocess": ["resize", "normalize", "augment"],
      "dataloader": {"batch_size": 256, "shuffle": true, "num_workers": 8}
    },
    "training": {
      "optimizer": "sgd",
      "lr": 0.1,
      "lr_schedule": "step",
      "weight_decay": 0.0001,
      "epochs": 90,
      "gradient_clip": 0,
      "mixed_precision": false,
      "batch_size": 256
    },
    "evaluation": {
      "metrics": ["accuracy", "loss"],
      "test_loop": true
    }
  },
  "files": {
    "model.py": ["BasicBlock", "Bottleneck", "ResNet"],
    "dataset.py": ["ImageNetDataset", "get_transforms"],
    "train.py": ["train_epoch", "train"],
    "evaluate.py": ["evaluate"]
  },
  "dependencies": ["torchvision"]
}
```

## Field Notes

- `submodules[].connections`: Describes data flow. Use this to verify tensor shapes are consistent.
- `submodules[].layers`: When > 1, generate a repeated block (e.g., 6 encoder layers).
- `loss`: Map to framework-specific implementation (`nn.CrossEntropyLoss` / `tf.keras.losses.SparseCategoricalCrossentropy`).
- `lr_schedule`: `warmup_cosine` is common in Transformers; `step` is common in CNNs.
- `files`: The generation order should respect dependencies — utils first, then model, then data, then train/eval.
