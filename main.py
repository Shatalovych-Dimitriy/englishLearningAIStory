import streamlit as st
import google.generativeai as genai
import time

# --- Налаштування ---
API_KEY = st.secrets["api_key"] # Розкоментуйте і вставте ключ, або налаштуйте змінні середовища
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Функція для розбиття списку на частини (chunks)
def chunk_list(data, size):
    return [data[i:i + size] for i in range(0, len(data), size)]

st.title("🎬 Vocab Series: Вивчаємо слова серіалом")

# Ввід списку слів (наприклад, 10-20 слів)
text_input = st.text_area(
    "Вставте сюди ваш список слів:", 
    "ambitious, hesitant, overcome, barrier, triumph, ancient, mysterious, scroll, decipher, secret, journey, unexpected, companion, betrayal, loyalty",
    height=150
)

words_per_chapter = st.slider("Скільки слів у кожному розділі?", 3, 10, 5)
genre = st.selectbox("Жанр історії:", ["Фентезі", "Кіберпанк", "Детектив", "Комедія"])

if st.button("Створити історію"):
    # Підготовка слів
    raw_words = [w.strip() for w in text_input.replace('\n', ',').split(',') if w.strip()]
    if not raw_words:
        st.error("Список слів порожній!")
    else:
        # Розбиваємо на групи
        word_chunks = chunk_list(raw_words, words_per_chapter)
        
        st.success(f"Знайдено {len(raw_words)} слів. Буде створено {len(word_chunks)} розділи(-ів).")
        
        # Змінна для зберігання контексту попередніх розділів
        story_context = ""
        full_story_display = ""

        # Прогрес-бар
        progress_bar = st.progress(0)

        for i, chunk in enumerate(word_chunks):
            chapter_num = i + 1
            current_words = ", ".join(chunk)
            
            with st.spinner(f"Пишу Розділ {chapter_num} із словами: {current_words}..."):
                
                # --- Розумний Промпт ---
                # Ми передаємо попередній контекст, щоб історія була цілісною
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
                
                try:
                    # Виклик AI (тут імітація, якщо немає ключа, розкоментуйте реальний виклик)
                    response = model.generate_content(prompt)
                    chapter_text = response.text

                    # Оновлюємо контекст (дуже простий спосіб - додаємо весь текст)
                    # Для дуже довгих історій краще просити AI робити саммарі попереднього, 
                    # але Gemini має велике вікно контексту, тому можна просто додавати текст.
                    story_context += chapter_text + "\n\n"
                    
                    # Виводимо розділ на екран
                    st.markdown(f"### 📖 Розділ {chapter_num}")
                    st.info(f"Слова: {current_words}")
                    st.markdown(chapter_text)
                    
                    # Робимо паузу, щоб не впертися в ліміти запитів (Rate Limits)
                    time.sleep(3) 
                    
                except Exception as e:
                    st.error(f"Помилка при генерації розділу {chapter_num}: {e}")
                    break
            
            # Оновлення прогрес-бару
            progress_bar.progress((i + 1) / len(word_chunks))

        st.balloons()
        st.markdown("---")
        st.markdown("### 📝 Повний текст для копіювання")
        st.text_area("Весь текст:", story_context, height=300)
