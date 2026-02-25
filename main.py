import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions
import time

# --- Налаштування ---
API_KEY = st.secrets["api_key"] 
genai.configure(api_key=API_KEY)

# --- СПИСОК МОДЕЛЕЙ ДЛЯ "КАРУСЕЛІ" ---
# Програма буде пробувати їх по черзі
MODEL_LIST = [
    'gemini-2.5-flash-lite',       # Спроба 1: Найновіша і найшвидша
    'models/gemini-2.0-flash',       # Спроба 2: Стабільна швидка
    'models/gemini-2.0-flash-lite',  # Спроба 3: Економна
    'models/gemini-2.0-flash-001',       # Спроба 4: Стандартна
    'models/gemini-1.5-pro'          # Спроба 5: Повільна, але якісна (резерв)
]

# --- ДІАГНОСТИКА МОДЕЛЕЙ ---
st.sidebar.header("🔧 Діагностика API")
if st.sidebar.button("Перевірити доступні моделі"):
    try:
        st.sidebar.write("Звертаюсь до Google...")
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        st.sidebar.success("Знайдено моделей: " + str(len(available_models)))
        st.sidebar.code("\n".join(available_models))
    except Exception as e:
        st.sidebar.error(f"Помилка доступу: {e}")

# --- ФУНКЦІЯ КАРУСЕЛІ (FALLBACK LOGIC) ---
def generate_with_fallback(prompt):
    # Проходимо по списку моделей
    for model_name in MODEL_LIST:
        try:
            # Створюємо модель "на льоту"
            active_model = genai.GenerativeModel(model_name)
            
            # Пробуємо отримати відповідь
            response = active_model.generate_content(prompt)
            return response, model_name # Повертаємо успіх і назву моделі
            
        except exceptions.ResourceExhausted:
            st.warning(f"⚠️ Модель {model_name} перевантажена. Перемикаюсь на наступну...")
            time.sleep(2) # Коротка пауза перед зміною моделі
            continue # Йдемо до наступної моделі в списку
            
        except Exception as e:
            # Якщо модель не знайдена або інша помилка - пробуємо наступну
            continue
            
    return None, None # Якщо всі моделі відмовили

# Функція для розбиття списку
def chunk_list(data, size):
    return [data[i:i + size] for i in range(0, len(data), size)]

# --- ІНТЕРФЕЙС ---
st.title("🎬 Vocab Series: Вивчаємо слова серіалом")

text_input = st.text_area(
    "Вставте сюди ваш список слів:", 
    "ambitious, hesitant, overcome, barrier, triumph, ancient, mysterious, scroll, decipher, secret, journey, unexpected, companion, betrayal, loyalty",
    height=150
)

words_per_chapter = st.slider("Скільки слів у кожному розділі?", 3, 10, 5)
genre = st.selectbox("Жанр історії:", ["Фентезі", "Кіберпанк", "Детектив", "Комедія"])

if st.button("Створити історію"):
    # Підготовка слів (обробка ком та нових рядків)
    raw_words = [w.strip() for w in text_input.replace('\n', ',').split(',') if w.strip()]
    
    if not raw_words:
        st.error("Список слів порожній!")
    else:
        # Розбиваємо на групи
        word_chunks = chunk_list(raw_words, words_per_chapter)
        
        st.success(f"Знайдено {len(raw_words)} слів. Буде створено {len(word_chunks)} розділи(-ів).")
        
        story_context = ""
        progress_bar = st.progress(0)

        # --- ГОЛОВНИЙ ЦИКЛ ---
        for i, chunk in enumerate(word_chunks):
            chapter_num = i + 1
            current_words = ", ".join(chunk)
            
            with st.spinner(f"Пишу Розділ {chapter_num} із словами: {current_words}..."):
                
                # --- ВАШ ПРОМПТ ---
                prompt = f"""
                You are a creative writer. Write **Chapter {chapter_num}** of a {genre} story.
                
                **Goal:** Integrate exactly these vocabulary words naturally: [{current_words}].
                **Requirements:**
                1. Highlight the vocabulary words in **bold**.
                2. Story continuity: This chapter must continue the plot from the previous summary (if any).
                3. Length: ~100-150 words per chapter.
                4. Level: B2 English.
                
                **Previous Context (Summary of what happened so far):**
                {story_context if story_context else "This is the beginning of the story."}
                
                **Output format:**
                Just the story text for this chapter. No intro like "Here is the story".
                """
                
                # Викликаємо функцію-карусель замість прямого виклику
                response, used_model = generate_with_fallback(prompt)
                
                if response and response.text:
                    chapter_text = response.text
                    
                    # Оновлюємо контекст
                    story_context += chapter_text + "\n\n"
                    
                    # Виводимо результат
                    st.markdown(f"### 📖 Розділ {chapter_num}")
                    st.caption(f"🤖 Згенеровано моделлю: `{used_model}`")
                    st.info(f"Слова: {current_words}")
                    st.markdown(chapter_text)
                    
                    # --- ВАЖЛИВА ПАУЗА ---
                    # 10 секунд, щоб не перевищити ліміт 15 запитів на хвилину
                    time.sleep(10) 
                    
                else:
                    st.error(f"❌ Не вдалося згенерувати розділ {chapter_num}. Можливо, вичерпано всі ліміти.")
                    break
            
            # Оновлення прогрес-бару
            progress_bar.progress((i + 1) / len(word_chunks))

        # Фінал
        st.balloons()
        st.markdown("---")
        st.markdown("### 📝 Повний текст для копіювання")
        st.text_area("Весь текст:", story_context, height=300)
