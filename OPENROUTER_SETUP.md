# OpenRouter Integration - ✅ Setup Guide

## Quick Start

Tu agente SomaAgent ahora soporta **dos LLM providers** con soporte completo:
- **Ollama**: Local, gratis, te controlas todo
- **OpenRouter**: Cloud-based con acceso a 300+ modelos

## Como usar OpenRouter

### Paso 1: Obtén tu API Key

1. Ve a https://openrouter.ai/settings/keys
2. Copia tu API key (comienza con `sk-or-...`)
3. **Guárdala en `.env`** (nunca en código)

### Paso 2: Configura `.env`

```env
# Selecciona el provider
LLM_PROVIDER=openrouter

# OpenRouter configuration
OPENROUTER_API_KEY=sk-or-v1-tu_clave_aqui
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-3.5-turbo
```

### Paso 3: Test local

```bash
# Activa el virtual env
.\.venv\Scripts\Activate.ps1

# Corre el test
python test_openrouter.py
```

**Espera ver:**
```
============================================================
OpenRouter Test Suite
============================================================

1️⃣  LANGCHAIN METHOD (recommended):
------------------------------------------------------------
[TEST] 🧪 Testing OpenRouter via LangChain ChatOpenAI...
[TEST] 🤖 Model: openai/gpt-3.5-turbo
[TEST] 🔗 Base: https://openrouter.ai/api/v1
[TEST] 🔑 API Key: ✓ CONFIGURED

[TEST] 📤 Initializing ChatOpenAI...
[TEST] 📝 Sending test prompt...
[TEST] ⏱️  Response time: 2.59s
[TEST] ✅ SUCCESS!
[TEST] 💬 Response: The movement 'golpear' in dance is a percussive strike...
[TEST] 🎉 OpenRouter via LangChain is working!
```

## APIs Importantes

| URL | Propósito |
|-----|-----------|
| `https://openrouter.ai/api/v1/chat/completions` | Chat API (lo que usamos) |
| `https://openrouter.ai/api/v1/models` | Listar modelos disponibles |

**IMPORTANTE:** Es `.ai` (no `.io`) ⚠️

## Modelos Recomendados

| Modelo | Velocidad | Calidad | Costo | Descrip |
|--------|-----------|---------|-------|---------|
| `openai/gpt-3.5-turbo` | ⚡ Rápido | 🟡 Bueno | 💰 Barato | Versátil |
| `google/gemini-2.0-flash-lite-preview-02-05` | ⚡⚡ Muy rápido | 🟢 Muy bueno | 💰 Muy barato | Vision |
| `meta-llama/llama-2-7b-chat` | ⚡ Rápido | 🟡 Bueno | 💰 Muy barato | Open source |
| `openai/gpt-4-turbo` | 🐢 Lento | 🟢⚡ Excelente | 💸 Caro | Power user |

Usa `openrouter/auto` para auto-selects el mejor modelo.

## Cómo cambiar providers

**Para usar Ollama (local, gratis):**
```env
LLM_PROVIDER=ollama
```
Luego restart tu agente.

**Para usar OpenRouter (cloud, pagado):**
```env
LLM_PROVIDER=openrouter
```
Luego restart tu agente.

## Qué cambió en el código

### 1. Imports en `reasoning.py`
```python
from config import (
    LLM_PROVIDER,
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL,
    OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_API_KEY,
)
```

### 2. Nuevas funciones
- `_call_openrouter()` - Usa LangChain ChatOpenAI
- `_call_llm()` - Wrapper que elige provider según config
- `_call_ollama()` - Intacto (compatible)

### 3. Cambios en `reasoning_node()`
```python
# Antes:
artistic_interpretation = _call_ollama(interpretation_prompt, timeout_sec=3)

# Ahora:
artistic_interpretation = _call_llm(interpretation_prompt, timeout_sec=5)
```

**✅ NADA fue eliminado** - Solo se agregaron opciones.

## Troubleshooting

### Error: "langchain-openai not installed"
```bash
pip install langchain-openai
```

### Error: "HTTP 405" o "Invalid API endpoint"
- ✅ URL correcta: `https://openrouter.ai/api/v1` (`.ai` no `.io`)
- ✅ Header: `Authorization: Bearer sk-or-...`
- ✅ Model format: `openai/gpt-3.5-turbo` (con `/`)

### Error: "401 Unauthorized"
- API key es inválida o expiró
- Genera una nueva en https://openrouter.ai/settings/keys

### Error: "429 Rate Limit"
- Estás haciendo muchos requests
- OpenRouter tiene límites según plan
- Espera unos segundos e intenta de nuevo

### Timeout sin respuesta
- Modelo está lento
- Intenta con modelo más rápido
- Aumenta `timeout_sec` en `_call_llm()`

## Próximos pasos

1. ✅ Test local pasa
2. Integra con `app.py` (cambiar provider en runtime)
3. Agrega logging de qué provider se usó
4. Deploy a Vercel
5. Monitorea costos en https://openrouter.ai/usage

## Referencias

- 📖 [OpenRouter Docs](https://openrouter.ai/docs)
- 🔑 [Get API Key](https://openrouter.ai/settings/keys)
- 📊 [Browse Models](https://openrouter.ai/models)
- 💰 [Pricing](https://openrouter.ai/pricing)
- 📈 [Usage Monitor](https://openrouter.ai/usage)
- ✅ [Request Builder](https://openrouter.ai/request-builder)

