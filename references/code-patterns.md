# Code Patterns Reference

Common PyTorch and TensorFlow patterns for paper-to-code generation. Read this file before generating code to ensure idiomatic, correct implementations.

---

## PyTorch Patterns

### Model Definition

```python
import torch
import torch.nn as nn

class MyModel(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.encoder = nn.Linear(config.input_dim, config.hidden_dim)
        self.decoder = nn.Linear(config.hidden_dim, config.output_dim)

    def forward(self, x):
        x = torch.relu(self.encoder(x))
        x = self.decoder(x)
        return x
```

### Training Loop

```python
def train_epoch(model, dataloader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    for batch_idx, (data, target) in enumerate(dataloader):
        data, target = data.to(device), target.to(device)

        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()

        if config.gradient_clip > 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.gradient_clip)

        optimizer.step()
        total_loss += loss.item()

    return total_loss / len(dataloader)
```

### Evaluation Loop

```python
@torch.no_grad()
def evaluate(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0
    correct = 0
    total = 0

    for data, target in dataloader:
        data, target = data.to(device), target.to(device)
        output = model(data)
        total_loss += criterion(output, target).item()
        pred = output.argmax(dim=1)
        correct += pred.eq(target).sum().item()
        total += target.size(0)

    return {"loss": total_loss / len(dataloader), "accuracy": correct / total}
```

### Dataset & DataLoader

```python
from torch.utils.data import Dataset, DataLoader

class MyDataset(Dataset):
    def __init__(self, data_path, transform=None):
        self.data = ...
        self.transform = transform

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        sample = self.data[idx]
        if self.transform:
            sample = self.transform(sample)
        return sample
```

### Multi-Head Attention

```python
class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, n_heads, dropout=0.1):
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads

        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)

    def scaled_dot_product_attention(self, Q, K, V, mask=None):
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        attn = torch.softmax(scores, dim=-1)
        attn = self.dropout(attn)
        return torch.matmul(attn, V)

    def forward(self, query, key, value, mask=None):
        batch_size = query.size(0)

        Q = self.W_q(query).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        K = self.W_k(key).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        V = self.W_v(value).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)

        attn_output = self.scaled_dot_product_attention(Q, K, V, mask)
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)
        return self.W_o(attn_output)
```

### Transformer Block

```python
class TransformerEncoderLayer(nn.Module):
    def __init__(self, d_model, n_heads, d_ff, dropout=0.1):
        super().__init__()
        self.attention = MultiHeadAttention(d_model, n_heads, dropout)
        self.feed_forward = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model)
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        attn_output = self.attention(x, x, x, mask)
        x = self.norm1(x + self.dropout(attn_output))
        ff_output = self.feed_forward(x)
        x = self.norm2(x + self.dropout(ff_output))
        return x
```

### Positional Encoding

```python
class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000, dropout=0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x):
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)
```

### Learning Rate Scheduler

```python
class WarmupCosineScheduler(torch.optim.lr_scheduler._LRScheduler):
    def __init__(self, optimizer, warmup_steps, total_steps, min_lr=0.0):
        self.warmup_steps = warmup_steps
        self.total_steps = total_steps
        self.min_lr = min_lr
        super().__init__(optimizer)

    def get_lr(self):
        step = self.last_epoch
        if step < self.warmup_steps:
            factor = step / max(1, self.warmup_steps)
        else:
            progress = (step - self.warmup_steps) / max(1, self.total_steps - self.warmup_steps)
            factor = 0.5 * (1 + math.cos(math.pi * progress))
        return [max(self.min_lr, base_lr * factor) for base_lr in self.base_lrs]
```

### Device Handling

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
```

### Mixed Precision Training

```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for data, target in dataloader:
    optimizer.zero_grad()
    with autocast():
        output = model(data)
        loss = criterion(output, target)
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

---

## TensorFlow Patterns

### Model Definition (Keras Subclassing)

```python
import tensorflow as tf
from tensorflow import keras

class MyModel(keras.Model):
    def __init__(self, config):
        super().__init__()
        self.encoder = keras.layers.Dense(config.hidden_dim, activation="relu")
        self.decoder = keras.layers.Dense(config.output_dim)

    def call(self, inputs, training=False):
        x = self.encoder(inputs)
        x = self.decoder(x)
        return x
```

### Training Loop (Custom)

```python
@tf.function
def train_step(model, data, target, optimizer, loss_fn):
    with tf.GradientTape() as tape:
        output = model(data, training=True)
        loss = loss_fn(target, output)
    gradients = tape.gradient(loss, model.trainable_variables)
    optimizer.apply_gradients(zip(gradients, model.trainable_variables))
    return loss
```

### Dataset (tf.data)

```python
def create_dataset(data_path, batch_size=32, shuffle=True):
    dataset = tf.data.Dataset.from_generator(
        lambda: data_generator(data_path),
        output_signature=(
            tf.TensorSpec(shape=(None, height, width, channels), dtype=tf.float32),
            tf.TensorSpec(shape=(None,), dtype=tf.int32)
        )
    )
    if shuffle:
        dataset = dataset.shuffle(buffer_size=1000)
    dataset = dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return dataset
```

### Device Handling

```python
strategy = tf.distribute.MirroredStrategy() if len(tf.config.list_physical_devices("GPU")) > 1 else None
```

---

## Common Checklist

When generating code, verify:

1. **Shape consistency**: Trace tensor shapes through every layer. Input shape → layer outputs → final shape must match IR.
2. **Imports**: Every class/function used must be imported. Check `torch.nn`, `torch.optim`, `torch.nn.functional`, etc.
3. **Loss function**: Must match IR's `components.model.loss` field exactly.
4. **Optimizer**: Must match IR's `components.training.optimizer` with correct hyperparameters.
5. **Device**: All tensors and models must be moved to the correct device.
6. **Train/eval mode**: Call `model.train()` before training, `model.eval()` before evaluation.
7. **Gradient zeroing**: `optimizer.zero_grad()` before `loss.backward()` (PyTorch).
8. **No gradient in eval**: Use `@torch.no_grad()` or `tf.no_grad()` in evaluation loops.
