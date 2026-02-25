import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions
import time

# --- Налаштування ---
API_KEY = st.secrets["api_key"] # Розкоментуйте і вставте ключ, або налаштуйте змінні середовища
genai.configure(api_key=API_KEY)
# --- ДІАГНОСТИКА МОДЕЛЕЙ (Початок) ---
st.sidebar.header("🔧 Діагностика API")

if st.sidebar.button("Перевірити доступні моделі"):
    try:
        st.sidebar.write("Звертаюсь до Google...")
        available_models = []
        
        # Запитуємо список усіх моделей
        for m in genai.list_models():
            # Нам потрібні тільки ті, що вміють генерувати текст ('generateContent')
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        # Виводимо список
        st.sidebar.success("Знайдено моделей: " + str(len(available_models)))
        st.sidebar.code("\n".join(available_models))
        
    except Exception as e:
        st.sidebar.error(f"Помилка доступу: {e}")
# --- ДІАГНОСТИКА МОДЕЛЕЙ (Кінець) ---
model = genai.GenerativeModel('gemini-2.0-flash')

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
# ... (початок коду такий самий) ...
        
        # Функція "розумного" запиту
        def generate_with_retry(model, prompt, max_retries=5):
            wait_time = 10 # Починаємо з 10 секунд очікування
            for attempt in range(max_retries):
                try:
                    return model.generate_content(prompt)
                except exceptions.ResourceExhausted: # Це помилка 429 (Quota)
                    st.warning(f"⏳ Ліміт запитів! Чекаємо {wait_time} секунд...")
                    time.sleep(wait_time)
                    wait_time *= 2 # Збільшуємо час очікування вдвічі (10 -> 20 -> 40...)
                except Exception as e:
                    st.error(f"Інша помилка: {e}")
                    return None
            return None # Якщо після 5 спроб нічого не вийшло

        # Головний цикл
        for i, chunk in enumerate(word_chunks):
            chapter_num = i + 1
            current_words = ", ".join(chunk)
            
            with st.spinner(f"Пишу Розділ {chapter_num} із словами: {current_words}..."):
                
                # ... (ВАШ ПРОМПТ ТУТ - залишається без змін) ...
                prompt = f"""You are a creative writer... (ваш промпт) ..."""

                # --- НОВА ЛОГІКА ВИКЛИКУ ---
                response = generate_with_retry(model, prompt)
                
                if response and response.text:
                    chapter_text = response.text
                    story_context += chapter_text + "\n\n"
                    
                    st.markdown(f"### 📖 Розділ {chapter_num}")
                    st.info(f"Слова: {current_words}")
                    st.markdown(chapter_text)
                else:
                    st.error("Не вдалося згенерувати розділ після кількох спроб. Спробуйте пізніше.")
                    break # Зупиняємо, щоб не мучити сервер
            
            # Стандартна пауза між успішними запитами (теж збільшена)
            time.sleep(2) 
            progress_bar.progress((i + 1) / len(word_chunks))

        st.balloons()
        st.markdown("---")
        st.markdown("### 📝 Повний текст для копіювання")
        st.text_area("Весь текст:", story_context, height=300)
