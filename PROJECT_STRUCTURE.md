# UFCA Student Support Agent - Project Structure

This document outlines the architecture and components of the WhatsApp support agent for UFCA students.

## 1. System Architecture Overview
The agent acts as an intelligent intermediary between UFCA's knowledge base and the student via WhatsApp (integrated via UChat).

## 2. Component Breakdown

### A. Inbound API & Identity Management
- **Source:** External API calls (UChat).
- **Identity Hashing:** User phone numbers are hashed to generate a unique, privacy-preserving `user_id`.
- **Session ID:** The hashed ID is used as the primary key for all session-related data.

### B. Memory System (State Management)
- **Technology:** Redis.
- **Mechanism:** Short-term memory storing a sliding window of the latest 3 to 5 message pairs (User Input vs. Agent Response).
- **Purpose:** Provide conversational context to the LLM for multi-turn interactions.

### C. Intent Classification (The Router)
Upon receiving a message, the LLM classifies the request into one of the following categories:
1. **General Info:** Academic processes, enrollment, etc.
2. **Links of Documents:** Direct links to forms, PDFs, or official pages.
3. **News:** Recent updates from UFCA.
4. **UR Menu:** The University Restaurant's weekly menu.
5. **Dangerous Requisition:** Malicious prompts or policy violations.

### D. RAG Mechanism (Knowledge Retrieval)
- **Vector Database:** Divided into distinct namespaces or collections based on the categories above (except for Dangerous Requisitions).
- **Retrieval Logic:**
    - If category is 1-4: Search the corresponding vector collection.
    - If category is 5: Trigger immediate safety protocol/rejection.

### E. Response Generation
- **Input:** User message + Redis context + Retrieved RAG data.
- **Output:** A concise, helpful response formatted for WhatsApp.

## 3. Data Flow
1. `UChat API` -> `Hashing Logic` -> `user_id`.
2. `user_id` -> `Redis` (Fetch history).
3. `User Message` + `History` -> `LLM Classifier`.
4. `Category` -> `Vector DB Query` (Targeted search).
5. `Retrieved Info` + `History` + `Message` -> `LLM Generator` -> `Final Response`.
6. `Final Response` -> `Redis` (Update history) & `UChat API` (Send to user).
