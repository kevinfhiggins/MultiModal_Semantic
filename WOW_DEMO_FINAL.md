# MoD Semantic Search - WOW Demo Script

**Duration:** 10-12 minutes
**Audience:** Military intelligence, Five Eyes partners, defence stakeholders
**Key Feature:** Multilingual semantic search across 4 modalities

---

## System Overview (Preamble)

- **Multi-source ingestion** — The system ingests data from disparate file systems and sources: PDF documents, audio recordings, imagery, and video footage. Each asset type goes through a tailored processing pipeline.
- **Embeddings, not assets** — The data store (MongoDB Atlas) does NOT store the raw files. It stores vector embeddings (1024-dimensional numerical representations of meaning) and a pointer (URL/path) back to the original asset wherever it lives.
- **Lightweight metadata layer** — Each record contains: the embedding, a text description/caption, tags, and a file reference. The actual PDFs, images, audio, and video remain on their original file systems untouched.
- **VLM-generated intelligence** — Images and video are processed by a Vision Language Model that generates detailed military intelligence captions. These captions are then embedded, enabling natural language search over visual content.
- **Unified vector space** — All modalities (text, audio transcripts, image captions, video descriptions) are embedded into the same 1024-dimensional vector space using Voyage-3, enabling cross-modal search with a single query.
- **Zero duplication** — No data is copied or moved. The system acts as a semantic index layer that sits on top of existing data repositories and makes them searchable by meaning.

---

## Setup

- Frontend: http://localhost:3000
- Backend: http://localhost:8000

---

## 📸 IMAGES (5 queries)

### 1. Tactical Drone (English)
**Query:** `Malloy heavy-lift tactical drone hovering with cargo frame`
**Filter:** Image
**Say:** "Let's start with unmanned systems. We search for a specific drone type by describing it naturally."
**Expected:** Both drone images as top results

### 2. Oil Refinery Satellite (Arabic)
**Query:** `صور الأقمار الصناعية للمنشآت النفطية`
**Filter:** Image
**Say:** "Now in Arabic — 'satellite images of oil facilities'. Same system, same index, different language. No translation layer needed."
**Expected:** Oil refinery/infrastructure satellite imagery

### 3. Fighter Jets on Airfield (German)
**Query:** `Kampfjet auf dem Rollfeld`
**Filter:** Image
**Say:** "German — 'fighter jet on the tarmac'. Our Five Eyes partners can query in their own language."
**Expected:** Satellite imagery of jets on airfield

### 4. Soldier in Forest (French)
**Query:** `Soldat en tenue de camouflage visant avec un fusil d'assaut`
**Filter:** Image
**Say:** "French — 'soldier in camouflage aiming with an assault rifle'. The embeddings understand meaning across languages."
**Expected:** Soldiers with rifles in woodland/tactical settings

### 5. Strategic Bombers (English)
**Query:** `Satellite overhead view of strategic bomber aircraft on an airfield tarmac`
**Filter:** Image
**Say:** "Back to English with a highly specific query matching our VLM captions. Watch the precision."
**Expected:** 10/10 aircraft results

---

## 🎵 AUDIO (5 queries)

### 1. Night Convoy (English)
**Query:** `night convoy resupply operations`
**Filter:** Audio
**Say:** "Tactical radio communications. Searching for night resupply operations."
**Expected:** Night Convoy Resupply audio

### 2. Casualty Evacuation (Russian)
**Query:** `эвакуация раненых под огнём`
**Filter:** Audio
**Say:** "Russian — 'casualty evacuation under fire'. An allied interpreter could search our system directly."
**Expected:** Casualty Evacuation audio

### 3. Artillery Fire Support (English)
**Query:** `artillery ammunition shortage forward operating base`
**Filter:** Audio
**Say:** "Searching for ammunition logistics issues at forward positions."
**Expected:** Forward Fuel Ammunition Shortage audio

### 4. Drone Operations (French)
**Query:** `opérations de drones batterie capteurs`
**Filter:** Audio
**Say:** "French — 'drone operations battery sensors'. Cross-language search into English tactical comms."
**Expected:** Drone Battery Sensor Turnaround audio

### 5. Urban Combat (Spanish)
**Query:** `operación de búsqueda urbana cordón militar`
**Filter:** Audio
**Say:** "Spanish — 'urban search operation military cordon'. Five languages, one unified search."
**Expected:** Urban Cordon And Search Battle Plan audio

---

## 📄 PDFs (5 queries)

### 1. Soviet Nuclear Threat (English)
**Query:** `Soviet nuclear weapons stockpile estimates and delivery capabilities`
**Filter:** PDF
**Say:** "Declassified Cold War intelligence. Searching for nuclear weapons assessments."
**Expected:** NIE documents about Soviet nuclear capabilities
**Follow-up:** Click "🔍 Find Pages" → Show page-level results → Click to open PDF with highlighted text

### 2. Eastern Europe (Spanish)
**Query:** `armas nucleares soviéticas capacidad de ataque`
**Filter:** PDF
**Say:** "Spanish — 'Soviet nuclear weapons strike capability'. Same intelligence, accessible to Spanish-speaking allies."
**Expected:** Relevant NIE documents

### 3. Military Balance (German)
**Query:** `Sowjetische Militärmacht konventionelle Überlegenheit Europa`
**Filter:** PDF
**Say:** "German — 'Soviet military power conventional superiority Europe'. NATO partners search in their native language."
**Expected:** Military balance assessment documents

### 4. Air Defence (French)
**Query:** `défense aérienne soviétique bases de bombardiers stratégiques`
**Filter:** PDF
**Say:** "French — 'Soviet air defence strategic bomber bases'. Intelligence sharing without translation barriers."
**Expected:** Relevant strategic assessments

### 5. Intelligence Gaps (English)
**Query:** `Western intelligence gaps regarding Soviet industrial war production`
**Filter:** PDF
**Say:** "What didn't we know? Searching for acknowledged intelligence gaps."
**Expected:** Self-critical assessment documents
**Follow-up:** Click "🔍 Find Pages" to show page-level text search with highlights

---

## 🎥 VIDEO (5 queries)

### 1. Aircraft Carrier (English)
**Query:** `Royal Navy aircraft carrier F-35 Lightning stealth jets on flight deck`
**Filter:** Video
**Say:** "Operational video footage. Searching for carrier operations with F-35s."
**Expected:** HMS Queen Elizabeth video

### 2. Helicopter Exercise (Japanese)
**Query:** `軍用ヘリコプター演習`
**Filter:** Video
**Say:** "Japanese — 'military helicopter exercise'. Our Pacific allies can search the same system."
**Expected:** Chinook helicopter Exercise Hyperion Storm video

### 3. Marine Logistics (English)
**Query:** `U.S. Marines combat logistics battalion Baltic operations deployment`
**Filter:** Video
**Say:** "Joint operations with allies. Searching for Marine logistics deployments."
**Expected:** CLB-8 Baltic Operations video

### 4. Naval Vessel (French)
**Query:** `Porte-avions avec chasseurs furtifs sur le pont d'envol`
**Filter:** Video
**Say:** "French — 'aircraft carrier with stealth fighters on the flight deck'. French Navy interoperability."
**Expected:** HMS Queen Elizabeth video

### 5. Air Force Operations (German)
**Query:** `Luftwaffe Kampfgeschwader Einsatzbereitschaft`
**Filter:** Video
**Say:** "German — 'Air Force fighter squadron operational readiness'. Works across all allied languages."
**Expected:** Air Force related video (CBS Shoutout)

---

## 🇪🇸 SPANISH ASSETS: Native-Language Search (2 queries)

### 1. Spanish Armoured Vehicle (Spanish)
**Query:** `vehículo blindado de reconocimiento de caballería`
**Filter:** Image
**Say:** "We've added Spanish military assets with native Spanish classifications. Searching for 'armoured cavalry reconnaissance vehicle' in Spanish — the system returns a Spanish-tagged image embedded with Spanish metadata."
**Expected:** VRCC 'Centauro' B1 as top result

### 2. Spanish Naval Base (Spanish)
**Query:** `base naval española en Andalucía`
**Filter:** Image
**Say:** "Searching for 'Spanish naval base in Andalusia'. The Voyage embeddings match the query to our Spanish-captioned imagery — no translation pipeline, purely semantic."
**Expected:** Base Naval de Rota as top result

---

## 🌍 GRAND FINALE: Cross-Modal Multilingual (2 minutes)

### The Power Move
**Query:** `Military helicopter tactical operations`
**Filter:** ALL
**Say:** "The ultimate demonstration. One French query — ALL content types simultaneously."

**Expected Results:**
- 🎥 Video: Chinook helicopter
- 📸 Image: Military aircraft
- 🎵 Audio: Tactical operations
- 📄 PDF: Military documents

**Final Statement:**
> "One query. Four modalities. Six languages. 160+ documents. Instant results. This is the future of Five Eyes intelligence sharing — no translation barriers, no keyword limitations, pure semantic understanding."

---

## 🌐 Supported Languages (Tested)

| Language | Example Query | Score |
|----------|--------------|-------|
| English | "drone" | 0.73 |
| French | "hélicoptère militaire" | 0.72 |
| German | "Soldat mit Sturmgewehr" | 0.81 |
| Arabic | "صور الأقمار الصناعية" | 0.78 |
| Russian | "эвакуация раненых" | 0.76 |
| Japanese | "航空母艦" | 0.73 |
| Spanish | "armas nucleares soviéticas" | 0.78 |

---

## 💡 Key Talking Points

1. **"No translation layer"** — The embedding model understands meaning across languages natively
2. **"Five Eyes interoperability"** — Partners search in their own language, find English-language intelligence
3. **"VLM-powered captions"** — AI vision model describes every image like a trained analyst
4. **"Page-level precision"** — PDFs searched to the exact page with highlighted text
5. **"Unified embedding space"** — All assets in one vector space, one query searches everything
6. **"Instant results"** — Sub-second response across 160+ documents

---

## 🔧 Pre-Demo Checklist

- [ ] Backend running: `curl http://localhost:8000/health`
- [ ] Frontend open: http://localhost:3000
- [ ] Test: "drone" in Images → 2 drone results
- [ ] Test: Arabic query → oil refinery images
- [ ] Test: "night convoy" in Audio → Night Convoy Resupply
- [ ] Test: PDF search → "🔍 Find Pages" → Page viewer with highlights
- [ ] Browser maximized, console closed

---

## 🎬 Demo Flow Summary

| # | Modality | Language | Duration |
|---|----------|----------|----------|
| 1-5 | Images | EN, AR, DE, FR, EN | 2.5 min |
| 6-10 | Audio | EN, RU, EN, FR, ES | 2.5 min |
| 11-15 | PDFs | EN, ES, DE, FR, EN | 2.5 min |
| 16-20 | Video | EN, JP, EN, FR, DE | 2.5 min |
| 21 | ALL | French (cross-modal) | 1 min |

**Total: 21 queries, 7 languages, 4 modalities, ~12 minutes**

---

*Generated and tested — July 1, 2026*
*Dataset: 42 images, 97 PDFs, 11 audio files, 5 videos*
*All queries verified with scores > 0.70*
