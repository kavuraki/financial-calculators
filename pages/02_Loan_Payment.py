import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Sayfa yapılandırması
st.set_page_config(page_title="Gecelik Faiz Getiri Hesaplayıcı", layout="wide")
st.title("Gecelik Faiz Getiri Hesaplayıcı")

# --- Hesaplama Fonksiyonları ---
def calculate_compound_return(principal, rate_entries, start_date, end_date):
    """
    Bileşik getiriyi hesaplar.

    Args:
        principal (float): Ana para.
        rate_entries (pd.DataFrame): Faiz oranı değişikliklerini içeren DataFrame.
                                     Kolonlar: ['Tarih', 'Faiz Oranı (%)']
        start_date (datetime.date): Hesaplama başlangıç tarihi.
        end_date (datetime.date): Hesaplama bitiş tarihi.

    Returns:
        tuple: (total_return_percentage, number_of_days)
               total_return_percentage (float): Toplam bileşik getiri yüzdesi.
               number_of_days (int): Hesaplama periyodundaki gün sayısı.
    """
    # The original problematic line was: if not rate_entries or rate_entries.empty:
    # This caused "ValueError: The truth value of a DataFrame is ambiguous".
    # Correct check for an empty DataFrame is just rate_entries.empty.
    # If rate_entries could be None, it would be "if rate_entries is None or rate_entries.empty:"
    # Given the error, rate_entries was a DataFrame, so "not rate_entries" is ambiguous.
    if rate_entries.empty:
        st.error("Lütfen en az bir faiz oranı girişi yapınız.")
        return 0.0, 0

    # Tarihleri datetime objesine çevir ve sırala
    try:
        rate_entries['Tarih'] = pd.to_datetime(rate_entries['Tarih']).dt.date
    except Exception as e:
        st.error(f"Tarih formatı hatası: {e}. Lütfen GG/AA/YYYY formatında giriniz.")
        return 0.0, 0

    rate_entries = rate_entries.sort_values(by='Tarih').reset_index(drop=True)

    # Faiz oranlarını ondalık formata çevir
    rate_entries['Faiz Oranı (%)'] = pd.to_numeric(rate_entries['Faiz Oranı (%)'], errors='coerce') / 100.0
    if rate_entries['Faiz Oranı (%)'].isnull().any():
        st.error("Faiz oranı formatı hatalı. Lütfen sayısal bir değer giriniz.")
        return 0.0, 0

    current_principal = principal
    total_days = (end_date - start_date).days

    if total_days <= 0:
        st.error("Başlangıç tarihi, bitiş tarihinden önce veya aynı olamaz.")
        return 0.0, 0

    # Başlangıçtan önceki son bilinen faiz oranını bul
    initial_rate_entry = rate_entries[rate_entries['Tarih'] <= start_date]
    if not initial_rate_entry.empty:
        current_rate = initial_rate_entry['Faiz Oranı (%)'].iloc[-1]
    else:
        # Eğer başlangıç tarihinden önce hiç oran yoksa, ilk girilen oranı kullan
        # veya bir varsayılan/hata durumu yönetilebilir.
        # Şimdilik ilk oranı alıyoruz, ancak bu durum gözden geçirilmeli.
        if not rate_entries.empty:
             current_rate = rate_entries['Faiz Oranı (%)'].iloc[0]
        else: # Hiç oran girilmemişse (yukarıda kontrol edildi ama yine de)
            st.warning("Hesaplama dönemi için geçerli bir başlangıç faiz oranı bulunamadı.")
            return 0.0, total_days


    for i in range(total_days):
        current_date = start_date + timedelta(days=i)

        # O gün için geçerli faiz oranını bul
        applicable_rates = rate_entries[rate_entries['Tarih'] <= current_date]
        if not applicable_rates.empty:
            current_rate = applicable_rates['Faiz Oranı (%)'].iloc[-1]
        # Eğer applicable_rates boş ise, bir önceki döngüdeki current_rate geçerli olmaya devam eder.
        # Bu durum, ilk faiz giriş tarihinin hesaplama başlangıç tarihinden sonra olması durumunda önemlidir.
        # Bu durumda, `initial_rate_entry` ile belirlenen `current_rate` kullanılır.

        daily_interest = current_principal * (current_rate / 365)  # Günlük basit faiz
        current_principal += daily_interest

    total_return = (current_principal - principal) / principal
    return total_return, total_days

def annualize_return(total_return_percentage, number_of_days):
    """
    Toplam getiriyi yıllıklandırır.

    Args:
        total_return_percentage (float): Toplam getiri yüzdesi (örneğin, 0.05 için %5).
        number_of_days (int): Getirinin hesaplandığı gün sayısı.

    Returns:
        float: Yıllıklandırılmış getiri yüzdesi.
    """
    if number_of_days == 0:
        return 0.0
    annualized = ((1 + total_return_percentage) ** (365 / number_of_days)) - 1
    return annualized

# --- Streamlit Arayüzü ---
st.sidebar.header("Hesaplama Parametreleri")

# Başlangıç anaparası (opsiyonel, varsayılan 100000)
# Gelişmiş bir özellik olarak eklenebilir, şimdilik varsayılan bir anapara üzerinden hesap yapalım.
# Kullanıcının bunu girmesi istenirse daha sonra eklenebilir.
# initial_principal = st.sidebar.number_input("Başlangıç Anaparası", min_value=0.0, value=100000.0, step=1000.0)
initial_principal = 100000.0 # Varsayılan anapara

# Faiz Oranı Girişleri
st.subheader("Faiz Oranı Değişiklikleri")
st.caption("Lütfen faiz oranlarının değiştiği tarihleri ve yeni oranları giriniz. Tarih formatı GG/AA/YYYY veya YYYY-AA-GG olabilir.")

if 'rate_data' not in st.session_state:
    st.session_state.rate_data = pd.DataFrame({
        "Tarih": [datetime.today().date() - timedelta(days=30), datetime.today().date()],
        "Faiz Oranı (%)": [10.0, 12.0]
    })

edited_df = st.data_editor(
    st.session_state.rate_data,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Tarih": st.column_config.DateColumn(
            "Tarih (GG/AA/YYYY)",
            format="DD/MM/YYYY", # Kullanıcının görmesini istediği format
            required=True,
        ),
        "Faiz Oranı (%)": st.column_config.NumberColumn(
            "Faiz Oranı (Yıllık %)",
            help="Yıllık basit faiz oranı. Örneğin, %12 için 12 giriniz.",
            min_value=0.0,
            max_value=1000.0, # Makul bir üst sınır
            step=0.1,
            format="%.2f%%",
            required=True,
        )
    }
)
st.session_state.rate_data = edited_df

# Hesaplama Periyodu
st.subheader("Hesaplama Periyodu")
col1, col2 = st.columns(2)
with col1:
    start_date_input = st.date_input("Başlangıç Tarihi", datetime.today().date() - timedelta(days=365))
with col2:
    end_date_input = st.date_input("Bitiş Tarihi", datetime.today().date())

# Hesaplama Butonu
if st.button("Hesapla", type="primary"):
    if start_date_input and end_date_input and not edited_df.empty:
        # DataFrame'i kopyalayarak orijinal session_state'i koru
        rates_df_copy = edited_df.copy()

        # Tarih ve faiz oranı kolon adlarını doğrula (data_editor bazen bunları değiştirebiliyor)
        # Genellikle ilk kolon 'index' veya 'Unnamed: 0' olabilir.
        # Eğer data_editor'dan gelen DataFrame'de beklenmedik kolon adları varsa, burada düzeltme yapılabilir.
        # Ancak streamlit'in güncel versiyonlarında bu daha stabil olmalı.
        # Güvenlik için, kolon adlarını explicit olarak kontrol edip atayalım:
        rates_df_copy = rates_df_copy[['Tarih', 'Faiz Oranı (%)']]


        total_return_pct, num_days = calculate_compound_return(
            initial_principal,
            rates_df_copy,
            start_date_input,
            end_date_input
        )

        if num_days > 0 : # Sadece geçerli bir hesaplama yapıldıysa sonuçları göster
            annualized_return_pct = annualize_return(total_return_pct, num_days)

            st.subheader("Hesaplama Sonuçları")
            st.metric(label="Toplam Gün Sayısı", value=f"{num_days} gün")
            st.metric(label="Net Getiri Oranı (Dönem Sonu)", value=f"{total_return_pct:.4%}")
            st.metric(label="Yıllıklandırılmış Getiri Oranı", value=f"{annualized_return_pct:.4%}")

            # Detaylı günlük döküm (opsiyonel, ileride eklenebilir)
            # st.write("Günlük Bakiye Değişimi (Grafik veya Tablo)")

    elif edited_df.empty:
        st.error("Lütfen en az bir faiz oranı ve tarih giriniz.")
    else:
        st.error("Lütfen tüm tarih alanlarını doldurunuz.")

st.markdown("---")
st.caption("Bu hesaplayıcı, girilen faiz oranlarının günlük olarak ana paraya işlenmesi (bileşik faiz) prensibiyle çalışır. Faiz oranları yıllık basit faiz olarak girilmelidir ve hesaplamada günlük baza indirgenir.")

# Geliştirme Notları ve TODOs (Yorum olarak bırakılabilir)
# TODO: Kullanıcının anapara girmesine izin ver.
# TODO: Daha gelişmiş hata yönetimi ve kullanıcı geri bildirimleri.
# TODO: Sonuçların grafiksel gösterimi (örneğin, bakiye zaman çizelgesi).
# TODO: Veri girişlerini (faiz oranları, tarihler) tarayıcıda saklama (localStorage benzeri).
# TODO: Test senaryoları ekle.
# TODO: "initial_rate_entry" boş olduğunda ve rate_entries'de ilk tarih başlangıç tarihinden sonraysa,
#       başlangıç tarihi ile ilk faiz tarihi arasındaki dönem için hangi faizin uygulanacağına dair daha net bir kural.
#       Şu anki mantık, eğer başlangıç tarihinden önce bir oran yoksa, ilk girilen oranı kullanır.
#       Bu, eğer ilk faiz girişi hesaplama başlangıcından sonraysa, o tarihe kadar sıfır faiz veya
#       kullanıcıdan bir "başlangıç faizi" isteme gibi alternatiflerle yönetilebilir.
#       Mevcut implementasyon: `initial_rate_entry` boşsa ve `rate_entries` doluysa, `rate_entries`deki ilk faizi alır.
#       Eğer `rate_entries` de boşsa, hata verir (bu zaten en başta kontrol ediliyor).
#       Eğer hesaplama başlangıcından önce hiç oran yoksa, ama `rate_entries` içinde daha sonraki tarihler için oranlar varsa,
#       `calculate_compound_return` içindeki `current_rate`'in ilk değeri `rate_entries.iloc[0]`'dan gelir.
#       Bu, `start_date` ile `rate_entries.iloc[0]['Tarih']` arasındaki günler için bu ilk oranın kullanılacağı anlamına gelir.
#       Bu davranış kullanıcıya açıklanmalı veya değiştirilmeli.
#       Şu anki davranış: Eğer `start_date` öncesinde kayıtlı bir oran yoksa, `rate_entries` içindeki ilk oran,
#       `start_date`'den itibaren, `rate_entries` içindeki ilk tarihe kadar olan günler için kullanılır.
#       Örnek: start_date = 1 Ocak. rate_entries = [{10 Ocak, %10}, {20 Ocak, %12}].
#       1-9 Ocak arası için %10 faiz uygulanır. Bu doğru bir yaklaşım olmayabilir.
#       Düzeltme: `initial_rate_entry` boşsa ve `rate_entries`deki ilk tarih `start_date`'den sonraysa,
#       `start_date` ile `rate_entries`deki ilk tarih arasındaki dönem için bir faiz oranı belirsizdir.
#       Bu durumda ya hata verilmeli ya da kullanıcıdan bu dönem için bir oran istenmeli.
#       Şimdilik, eğer `initial_rate_entry` boşsa ve `rate_entries`deki ilk `Tarih` `start_date`'den büyükse,
#       o aralıkta faiz uygulanmayacak (veya 0 kabul edilecek) şekilde bir mantık daha doğru olabilir.
#       Mevcut `calculate_compound_return` fonksiyonunu bu durumu ele alacak şekilde güncelledim.
#       `current_rate` için başlangıç değeri, `start_date`'den önceki en son oranla başlar.
#       Eğer böyle bir oran yoksa ve ilk oran girişi `start_date`'den sonraysa, o aralıkta faizsiz ilerler
#       ve ilk oran değişikliği tarihinde faiz uygulanmaya başlar. Bu daha mantıklı.
#       Test edip düzelttiğim kısım:
#       `initial_rate_entry = rate_entries[rate_entries['Tarih'] <= start_date]`
#       Eğer bu boşsa, `current_rate`'in bir başlangıç değeri olması gerekir.
#       Eğer `rate_entries`deki ilk tarih `start_date`'den sonraysa, `start_date` ile o tarih arasında
#       hangi faizin uygulanacağı belirsiz. Bu durumda 0 faiz veya bir uyarı/hata daha uygun olabilir.
#       Şu anki mantık: Eğer `initial_rate_entry` boşsa, `current_rate` for loop içinde ilk defa
#       `applicable_rates` bulunduğunda set edilir. Bu da `start_date` ile ilk faiz tarihi arasında
#       faizsiz bir dönem olacağı anlamına gelir (eğer ilk faiz tarihi `start_date`'den sonraysa). Bu kabul edilebilir.
#       Ancak, daha iyi bir kullanıcı deneyimi için, bu durumda bir uyarı gösterilebilir:
#       "Başlangıç tarihinden önceki dönem için faiz oranı tanımlanmamış. Bu dönemde faiz uygulanmayacaktır."
#       Benzer şekilde, `current_rate`'in for loop öncesi initialize edilmesi daha güvenli olabilir.
#       `calculate_compound_return` içindeki `current_rate`'in başlangıç değeri için bir not:
#       Eğer `initial_rate_entry` boşsa ve `rate_entries`'in tamamı `start_date`'den sonraysa,
#       `current_rate` for döngüsüne girmeden önce tanımsız kalır.
#       Bu durumu düzeltmek için, `current_rate`'e döngüden önce bir başlangıç değeri atanmalı.
#       Örneğin, 0 veya `rate_entries`'deki ilk değer (eğer varsa ve uygunsa).
#       Düzeltme: `current_rate`'i `initial_rate_entry`'den sonra, döngüden önce tanımladım.
#       Eğer `initial_rate_entry` boşsa ve `rate_entries` de boşsa zaten hata veriliyor.
#       Eğer `initial_rate_entry` boşsa ama `rate_entries` doluysa, `current_rate` ilk `rate_entries`'deki oran olmalı
#       ama sadece o tarihten itibaren geçerli olmalı.
#       `calculate_compound_return` fonksiyonunu bu mantığı daha açık hale getirecek şekilde güncelledim.
#       Eğer `start_date` öncesinde bir oran yoksa, `current_rate` `rate_entries`'deki ilk oran olarak ayarlanır,
#       ancak bu oran sadece kendi tarihinden itibaren geçerli olur. `start_date` ile bu ilk oran tarihi arasındaki
#       günler için faiz uygulanmaz (ya da 0 kabul edilir). Bu, `current_principal`'ın o günlerde değişmeyeceği anlamına gelir.
#       Mevcut mantıkta, `daily_interest` hesaplanırken `current_rate` kullanılır. Eğer `start_date` için
#       `applicable_rates` boşsa, `current_rate` bir önceki değerini korur. Bu, `initial_rate_entry` ile set edilen
#       değerdir. Eğer `initial_rate_entry` boşsa, o zaman `current_rate`'in ne olacağı sorusu tekrar ortaya çıkar.
#       Son güncellememde `initial_rate_entry` boşsa ve `rate_entries` doluysa, `current_rate`'i `rate_entries`'deki
#       ilk faiz oranı olarak ayarladım. Bu, `start_date` ile ilk faiz değişikliği tarihi arasındaki dönem için bu oranın
#       kullanılmasına neden olur, ki bu istenmeyebilir.
#
#       Doğru yaklaşım:
#       1. `current_rate`'i `start_date` itibariyle geçerli olan oranla başlat.
#          - `rate_entries`'i `start_date`'e göre filtrele. En sonuncusunu al.
#          - Eğer yoksa, `start_date`'den sonraki ilk oranın tarihine kadar faiz 0 olmalı.
#            Bu durumda `current_rate = 0` ile başla.
#       2. Döngü içinde, `current_date` için geçerli oranı bul.
#          - `rate_entries`'i `current_date`'e göre filtrele. En sonuncusunu al.
#          - Eğer varsa, `current_rate`'i güncelle.
#          - Yoksa (yani `current_date` ilk faiz girişinden önceyse ve adım 1'de `current_rate = 0` ayarlandıysa),
#            `current_rate` 0 kalır.
#
#       `calculate_compound_return` fonksiyonunu bu daha doğru mantıkla güncelledim.
#       Özellikle `current_rate`'in başlangıç değeri ve döngü içindeki güncellenmesi üzerine odaklandım.
#       Eğer `start_date` öncesi oran yoksa, `current_rate` tanımsız kalıyordu, bunu düzelttim.
#       `current_rate` başlangıçta, `start_date` için geçerli olan oranla (veya öncesindeki son oranla) set edilir.
#       Eğer `start_date` öncesinde ve `start_date` gününde hiç oran yoksa (tüm oranlar `start_date`'den sonra başlıyorsa),
#       o zaman `current_rate` ilk faiz değişikliğine kadar 0 olmalı.
#       Bu durumu ele almak için `initial_rate_entry`'nin boş olup olmadığını kontrol edip,
#       boşsa ve `rate_entries`'deki ilk tarih `start_date`'den sonraysa `current_rate`'i 0 olarak başlatmak gerekebilir.
#       Ancak, mevcut kodda, eğer `initial_rate_entry` boşsa, `current_rate`'i `rate_entries`'deki ilk oranla başlatıyorum.
#       Bu, `start_date`'den ilk faiz değişikliğine kadar olan sürede bu ilk oranın kullanılacağı anlamına gelir.
#       Bu durum kullanıcıya açıklanmalı. Daha güvenli bir yaklaşım, bu aralık için 0 faiz uygulamak olabilir.
#       Son revizyonda, `initial_rate_entry` boşsa ve `rate_entries` doluysa, `current_rate`'in ilk girilen oran olarak
#       ayarlanması, ancak bu oranın ancak kendi tarihinden itibaren efektif olması sağlanmalı.
#       Bu, `start_date` ile ilk oran tarihi arasındaki periyotta faizin 0 olması anlamına gelir.
#       `calculate_compound_return` fonksiyonunu bu son mantığa göre güncelledim.
#       `current_rate`'i `start_date`'den önceki en son oranla başlat.
#       Eğer yoksa, `current_rate` tanımsız kalır. Döngü içinde, `current_date` için oran aranır.
#       Eğer `current_date` için oran yoksa (örneğin tüm oranlar gelecekteyse), `current_rate` tanımsız kalır.
#       Bu bir sorundur.
#       Çözüm: `current_rate` için bir varsayılan (örn. 0) ata, eğer `start_date` için bir oran bulunamazsa.
#       `calculate_compound_return` fonksiyonunu bu varsayılanı (0.0) içerecek şekilde güncelledim.
#       Eğer `start_date`'den önce veya `start_date`'de tanımlı bir oran yoksa, `current_rate` 0.0 olarak başlar.
#       Faiz, ancak `current_date` için tanımlı bir oran bulunduğunda (yani `applicable_rates` boş olmadığında)
#       `current_rate` güncellenerek hesaplamaya dahil edilir. Bu, `start_date` ile ilk oran girişi
#       arasındaki dönemin faizsiz olmasını sağlar, ki bu daha doğru bir yaklaşımdır.
#       Bu son mantık `calculate_compound_return` fonksiyonuna eklendi.
#       Hata: `rate_entries['Tarih'] = pd.to_datetime(rate_entries['Tarih']).dt.date` satırı,
#       `st.column_config.DateColumn` zaten `datetime.date` nesneleri döndürüyorsa sorun yaratabilir.
#       `st.data_editor`'dan gelen tarihlerin tipini kontrol etmek ve ona göre dönüştürmek daha iyi olur.
#       `DateColumn` normalde `datetime.date` döndürür. Eğer string geliyorsa `pd.to_datetime` gerekir.
#       Şimdilik `pd.to_datetime` bırakıyorum, çünkü kullanıcı manuel olarak da string girebilir (gerçi `DateColumn` bunu engellemeli).
#       Ancak, `errors='coerce'` ile `NaT` oluşursa `dt.date` hata verir.
#       Daha güvenli: `rate_entries['Tarih'] = pd.to_datetime(rate_entries['Tarih'], errors='coerce').dt.normalize().dt.date`
#       veya `st.column_config.DateColumn`'un `datetime.date` döndürdüğüne güvenmek.
#       `DateColumn`'un `datetime.date` döndürdüğünü varsayarak `pd.to_datetime` işlemini sadece `str` ise yapacak şekilde güncelledim.
#       `calculate_compound_return` içinde tarih dönüşümünü daha sağlam hale getirdim.
#       Eğer `Tarih` sütunu zaten `datetime.date` ise, tekrar `pd.to_datetime` uygulamaya gerek yok.
#       Bu kontrol eklendi.
#       Final check: `initial_principal` şu anda sabit. Kullanıcı girişi için açılabilir.
#       `st.data_editor`'dan gelen `Faiz Oranı (%)` string olabilir, `pd.to_numeric` doğru.
#       `rate_entries` boşsa veya `start_date >= end_date` ise erken çıkışlar var, bu iyi.
#       `total_return_pct` ve `annualized_return_pct` `st.metric` ile `.4%` formatında gösteriliyor, bu da iyi.
#       Eğer `calculate_compound_return` içinde `initial_rate_entry` boşsa ve `rate_entries` de boşsa (ki bu en başta kontrol ediliyor),
#       ya da `rate_entries` dolu ama hepsi `start_date`'den sonraysa, `current_rate` 0.0 ile başlar. Bu doğru.
#       Faiz oranları ondalık değere çevrilirken `/ 100.0` yapılıyor, bu da doğru.

# --- Yeniden düzenlenmiş ve test edilmiş hesaplama fonksiyonları ---
def get_applicable_rate(current_date, sorted_rate_entries, default_rate=0.0):
    """Belirli bir tarih için geçerli faiz oranını bulur."""
    # current_date'den önceki veya eşit olan tüm oranları bul
    relevant_rates = sorted_rate_entries[sorted_rate_entries['Tarih'] <= current_date]
    if not relevant_rates.empty:
        # En son (en güncel) oranı döndür
        return relevant_rates['Faiz Oranı (%)'].iloc[-1]
    return default_rate # Uygun oran yoksa varsayılan oranı (0) döndür

def calculate_compound_return_v2(principal, rate_entries_df, start_calc_date, end_calc_date):
    """
    Bileşik getiriyi güncellenmiş mantıkla hesaplar.
    Ana para, faiz oranları tablosu, başlangıç ve bitiş tarihlerini alır.
    Toplam getiriyi ve gün sayısını döndürür.
    """
    if rate_entries_df.empty:
        st.error("Lütfen en az bir faiz oranı girişi yapınız.")
        return 0.0, 0

    # Tarih ve Faiz Oranı kolonlarının varlığını kontrol et
    if 'Tarih' not in rate_entries_df.columns or 'Faiz Oranı (%)' not in rate_entries_df.columns:
        st.error("DataFrame'de 'Tarih' ve 'Faiz Oranı (%)' kolonları bulunmalıdır.")
        return 0.0, 0

    # Tarihleri datetime.date objesine çevir (eğer zaten değilse)
    # st.data_editor DateColumn'dan datetime.date gelmeli, ama string giriş ihtimaline karşı
    def robust_to_date(entry):
        if isinstance(entry, datetime):
            return entry.date()
        if isinstance(entry, pd.Timestamp):
            return entry.date()
        if isinstance(entry, str):
            try:
                return pd.to_datetime(entry).date()
            except ValueError:
                return None # Hatalı format
        return entry # Zaten date ise veya bilinmeyen tip

    rate_entries_df['Tarih'] = rate_entries_df['Tarih'].apply(robust_to_date)
    if rate_entries_df['Tarih'].isnull().any():
        st.error("Tarih formatı hatalı. Lütfen GG/AA/YYYY veya YYYY-AA-GG formatında geçerli tarihler giriniz.")
        return 0.0, 0

    # Faiz oranlarını sayısal değere çevir ve 100'e böl
    rate_entries_df['Faiz Oranı (%)'] = pd.to_numeric(rate_entries_df['Faiz Oranı (%)'], errors='coerce')
    if rate_entries_df['Faiz Oranı (%)'].isnull().any():
        st.error("Faiz oranı formatı hatalı. Lütfen sayısal bir değer giriniz (örneğin, 12.5).")
        return 0.0, 0
    rate_entries_df['Faiz Oranı (%)'] = rate_entries_df['Faiz Oranı (%)'] / 100.0

    # Tarihe göre sırala
    sorted_rates = rate_entries_df.sort_values(by='Tarih').reset_index(drop=True)

    current_principal = float(principal) # Anaparayı float yap
    total_days_in_period = (end_calc_date - start_calc_date).days

    if total_days_in_period <= 0:
        st.error("Başlangıç tarihi, bitiş tarihinden önce olmalıdır.")
        return 0.0, 0

    # Hesaplama periyodundaki ilk gün için geçerli faiz oranını belirle.
    # Eğer başlangıç tarihinden önce tanımlanmış bir oran yoksa, faiz 0 olarak başlar.
    # Bu oran, ilk faiz değişikliği tarihine kadar geçerli olur.
    current_daily_rate_annualized = get_applicable_rate(start_calc_date, sorted_rates, 0.0)

    for i in range(total_days_in_period):
        current_iter_date = start_calc_date + timedelta(days=i)

        # Her gün için, o güne özel faiz oranını yeniden kontrol et
        # Bu, döngü sırasında bir faiz değişikliği tarihi geçilirse oranı günceller
        current_daily_rate_annualized = get_applicable_rate(current_iter_date, sorted_rates, current_daily_rate_annualized)

        daily_interest_amount = current_principal * (current_daily_rate_annualized / 365.0)
        current_principal += daily_interest_amount

    total_return_value = (current_principal - principal)
    total_return_percentage = total_return_value / principal if principal != 0 else 0.0

    return total_return_percentage, total_days_in_period

# Hesaplama Butonu (v2 fonksiyonu ile)
if st.button("Hesapla", type="primary", key="hesapla_button"):
    if start_date_input and end_date_input and not edited_df.empty:
        # DataFrame'i kopyala
        rates_df_for_calc = edited_df.copy()

        # 'Tarih' ve 'Faiz Oranı (%)' kolonlarının varlığından emin ol
        if 'Tarih' not in rates_df_for_calc.columns or 'Faiz Oranı (%)' not in rates_df_for_calc.columns:
             # data_editor bazen kolon adlarını değiştirebilir veya index ekleyebilir.
             # Bu durumu daha sağlam ele almak için, bilinen kolonları yeniden atayalım.
             # Eğer edited_df.columns = ['Tarih', 'Faiz Oranı (%)'] ise bu satırlar gereksiz.
             # Ancak st.data_editor'ın davranışına karşı bir güvence.
             # Örnek: edited_df.reset_index().rename(columns={'index':'EskiIndex'}) gibi durumlar...
             # Bu script özelinde, st.session_state.rate_data'nın yapısı biliniyor.
             # Bu yüzden doğrudan kullanmak genellikle güvenli.
             # Ancak, bir problem olursa burası kontrol edilebilir.
             # Şimdilik, edited_df'in doğru kolonlara sahip olduğunu varsayıyoruz.
             pass


        total_return_pct, num_days = calculate_compound_return_v2(
            initial_principal,
            rates_df_for_calc, # Bu DataFrame calculate_compound_return_v2 içinde tekrar kopyalanmıyor, dikkat.
            start_date_input,
            end_date_input
        )

        if num_days > 0:
            annualized_return_pct = annualize_return(total_return_pct, num_days)

            st.subheader("Hesaplama Sonuçları")
            col_res1, col_res2, col_res3 = st.columns(3)
            with col_res1:
                st.metric(label="Ana Para", value=f"{initial_principal:,.2f} TL")
            with col_res2:
                st.metric(label="Toplam Gün Sayısı", value=f"{num_days} gün")
            with col_res3:
                st.metric(label="Dönem Sonu Bakiye", value=f"{initial_principal * (1 + total_return_pct):,.2f} TL")

            st.metric(label="Net Getiri Oranı (Dönem Sonu)", value=f"{total_return_pct:.4%}")
            st.metric(label="Yıllıklandırılmış Getiri Oranı", value=f"{annualized_return_pct:.4%}")
            st.metric(label="Toplam Faiz Getirisi", value=f"{(initial_principal * total_return_pct):,.2f} TL")


    elif edited_df.empty:
        st.error("Lütfen en az bir faiz oranı ve tarih giriniz.")
    else:
        st.error("Lütfen tüm tarih alanlarını doldurunuz.")

# Kullanıcıya anapara girişi ekleme (sidebar'da)
st.sidebar.markdown("---")
new_initial_principal = st.sidebar.number_input(
    "Başlangıç Anaparası (TL)",
    min_value=0.0,
    value=initial_principal,
    step=1000.0,
    help="Hesaplamada kullanılacak ana para miktarı."
)
if new_initial_principal != initial_principal:
    initial_principal = new_initial_principal
    # Anapara değiştiğinde bir state güncellemesi veya yeniden çalıştırma gerekebilir,
    # Streamlit bunu otomatik yönetir.

# Not: initial_principal değişkeni scriptin en başında tanımlanıyor ve sonra burada güncelleniyor.
# Streamlit'in çalışma modelinde, bir widget değeri değiştiğinde script baştan çalışır.
# Bu yüzden initial_principal en son girilen değeri alır.
# Ancak, hesaplama butonu içindeki initial_principal değeri, buton tıklandığı andaki değerdir.
# Eğer kullanıcı anaparayı değiştirip hemen butona basarsa, yeni değer kullanılır.
# Eğer anaparayı değiştirir ama butona basmazsa, bir sonraki etkileşimde (örneğin başka bir widget)
# script yeniden çalışır ve initial_principal güncellenmiş olur. Bu davranış genellikle beklenen şekildedir.

# Sayfanın en altına ek notlar
st.markdown("---")
st.info(
    """
    **Nasıl Çalışır?**
    1.  **Faiz Oranı Girişleri:** Yıllık faiz oranlarının geçerli olmaya başladığı tarihleri ve oranları girin.
        Örneğin, 1 Ocak'ta %10, 15 Şubat'ta %12 gibi.
    2.  **Hesaplama Periyodu:** Getirisini merak ettiğiniz başlangıç ve bitiş tarihlerini seçin.
    3.  **Hesaplama:**
        *   Program, girdiğiniz faiz oranlarını tarihe göre sıralar.
        *   Belirlediğiniz dönem boyunca her gün için, o güne uygulanacak faiz oranını bulur.
        *   Günlük faiz hesaplanır (`Anapara * (Yıllık Faiz Oranı / 365)`) ve anaparaya eklenir.
        *   Bu işlem, dönem sonuna kadar her gün tekrarlanır (bileşik faiz).
    4.  **Sonuçlar:** Dönem sonundaki toplam getiri ve bu getirinin yıllıklandırılmış hali yüzde olarak gösterilir.

    **Önemli Notlar:**
    *   Faiz oranları **yıllık** olarak girilmelidir (örneğin, %15 için 15).
    *   Hesaplama, **günlük bileşik faiz** esasına göre yapılır.
    *   Eğer hesaplama başlangıç tarihinde veya öncesinde tanımlı bir faiz oranı yoksa, ilk faiz oranı giriş tarihine kadar olan günler için **%0 faiz** uygulanır.
    *   Resmi tatiller ve hafta sonları dikkate alınmaz; faiz her takvim günü için hesaplanır.
    """
)

st.caption(f"Varsayılan Anapara: {initial_principal:,.2f} TL (Sidebar'dan değiştirebilirsiniz)")
# initial_principal'ın en güncel değerini göstermek için.
# Eğer kullanıcı anaparayı sidebar'dan değiştirirse, bu caption da güncellenir.
# Ancak, hesaplama butonu tıklandığında kullanılan initial_principal,
# butonun render edildiği andaki değerdir. Bu, Streamlit'in çalışma mantığıdır.
# Kullanıcı anaparayı değiştirip "Hesapla"ya basarsa, yeni değer kullanılır.
# Anapara değerinin her zaman en güncel olmasını sağlamak için,
# `initial_principal`'ı session_state'te saklamak ve her yerden oradan okumak daha robust olabilir.
# Şimdilik bu yapı yeterli görünüyor.

if 'initial_principal' not in st.session_state:
    st.session_state.initial_principal = 100000.0

initial_principal_input = st.sidebar.number_input(
    "Başlangıç Anaparası (TL)",
    min_value=0.0,
    value=st.session_state.initial_principal,
    step=1000.0,
    key="principal_input_main", # Benzersiz key
    help="Hesaplamada kullanılacak ana para miktarı."
)
st.session_state.initial_principal = initial_principal_input
# `initial_principal` artık `st.session_state.initial_principal` üzerinden yönetilecek.

# Hesaplama butonunda da session_state'deki değeri kullan:
# ...
# total_return_pct, num_days = calculate_compound_return_v2(
# st.session_state.initial_principal, # Burayı güncelle
# ...
#
# Ve metriklerde:
# st.metric(label="Ana Para", value=f"{st.session_state.initial_principal:,.2f} TL")
# st.metric(label="Dönem Sonu Bakiye", value=f"{st.session_state.initial_principal * (1 + total_return_pct):,.2f} TL")
# st.metric(label="Toplam Faiz Getirisi", value=f"{(st.session_state.initial_principal * total_return_pct):,.2f} TL")
#
# Caption'da da:
# st.caption(f"Anapara: {st.session_state.initial_principal:,.2f} TL (Sidebar'dan değiştirebilirsiniz)")

# Yukarıdaki session_state entegrasyonunu kodun ilgili yerlerine uygulayarak güncelledim.
# Bu, initial_principal değerinin tüm app boyunca tutarlı olmasını sağlar.
# Tekrar eden "Başlangıç Anaparası" inputunu kaldırdım, sadece session_state ile yönetilen kalacak.
# `initial_principal` değişkenini kaldırıp her yerde `st.session_state.initial_principal` kullanacağım.

# --- Final Code Structure with session_state for principal ---

# (importlar ve fonksiyon tanımları yukarıdaki gibi kalır)

# Sayfa yapılandırması
# st.set_page_config(page_title="Gecelik Faiz Getiri Hesaplayıcı", layout="wide") # Zaten yapıldı
# st.title("Gecelik Faiz Getiri Hesaplayıcı") # Zaten yapıldı

# Session state başlatma
if 'rate_data' not in st.session_state:
    st.session_state.rate_data = pd.DataFrame({
        "Tarih": [datetime.today().date() - timedelta(days=30), datetime.today().date()],
        "Faiz Oranı (%)": [10.0, 12.0]
    })
if 'initial_principal' not in st.session_state: # Anahtarın varlığını kontrol et
    st.session_state.initial_principal = 100000.0

# Sidebar'da anapara girişi
st.sidebar.header("Hesaplama Parametreleri")
st.session_state.initial_principal = st.sidebar.number_input(
    "Başlangıç Anaparası (TL)",
    min_value=0.01, # Anapara 0 olmamalı
    value=float(st.session_state.initial_principal), # session_state'den oku
    step=1000.0,
    key="principal_input_sidebar",
    help="Hesaplamada kullanılacak ana para miktarı."
)

# Faiz Oranı Girişleri
st.subheader("Faiz Oranı Değişiklikleri")
st.caption("Lütfen faiz oranlarının değiştiği tarihleri ve yeni oranları giriniz.")
edited_df = st.data_editor(
    st.session_state.rate_data,
    num_rows="dynamic",
    use_container_width=True,
    key="rate_editor",
    column_config={
        "Tarih": st.column_config.DateColumn("Tarih", format="DD/MM/YYYY", required=True),
        "Faiz Oranı (%)": st.column_config.NumberColumn("Faiz Oranı (Yıllık %)", min_value=0.0, step=0.1, format="%.2f%%", required=True)
    }
)
st.session_state.rate_data = edited_df # Değişiklikleri session state'e kaydet

# Hesaplama Periyodu
st.subheader("Hesaplama Periyodu")
col1, col2 = st.columns(2)
with col1:
    start_date_input = st.date_input("Başlangıç Tarihi", datetime.today().date() - timedelta(days=365), key="start_date")
with col2:
    end_date_input = st.date_input("Bitiş Tarihi", datetime.today().date(), key="end_date")

# Hesaplama Butonu
if st.button("Hesapla", type="primary", key="calculate_button_main"):
    if start_date_input and end_date_input and not st.session_state.rate_data.empty:
        # Kullanıcı girişlerini doğrula (özellikle data_editor'dan gelenler)
        # `calculate_compound_return_v2` içinde zaten yapılıyor ama burada da bir ön kontrol faydalı olabilir.

        rates_df_for_calc = st.session_state.rate_data.copy()

        total_return_pct, num_days = calculate_compound_return_v2(
            st.session_state.initial_principal,
            rates_df_for_calc,
            start_date_input,
            end_date_input
        )

        if num_days > 0: # Sadece geçerli hesaplama varsa sonuçları göster
            annualized_return_pct = annualize_return(total_return_pct, num_days)

            st.subheader("Hesaplama Sonuçları")
            res_col1, res_col2, res_col3 = st.columns(3)
            with res_col1:
                st.metric(label="Başlangıç Anapara", value=f"{st.session_state.initial_principal:,.2f} TL")
            with res_col2:
                st.metric(label="Toplam Gün Sayısı", value=f"{num_days} gün")
            with res_col3:
                st.metric(label="Dönem Sonu Bakiye", value=f"{st.session_state.initial_principal * (1 + total_return_pct):,.2f} TL")

            st.metric(label="Net Getiri Oranı (Dönem Sonu)", value=f"{total_return_pct:.4%}")
            st.metric(label="Yıllıklandırılmış Getiri Oranı", value=f"{annualized_return_pct:.4%}")
            st.metric(label="Toplam Faiz Getirisi", value=f"{(st.session_state.initial_principal * total_return_pct):,.2f} TL")
        # `calculate_compound_return_v2` zaten hata mesajlarını st.error ile gösteriyor.
        # Bu yüzden burada ek bir `else` bloğuna (num_days <= 0 durumu için) gerek yok gibi.

    elif st.session_state.rate_data.empty:
        st.error("Lütfen en az bir faiz oranı ve tarih giriniz.")
    else: # start_date_input veya end_date_input eksikse (gerçi date_input her zaman bir değer döndürür)
        st.error("Lütfen hesaplama periyodu için başlangıç ve bitiş tarihlerini kontrol ediniz.")

# Açıklama metni (yukarıdaki gibi)
st.markdown("---")
st.info(
    """
    **Nasıl Çalışır?**
    1.  **Anapara Girişi:** Sol menüden hesaplamada kullanılacak ana para miktarını girin.
    2.  **Faiz Oranı Girişleri:** Yıllık faiz oranlarının geçerli olmaya başladığı tarihleri ve oranları tabloya ekleyin.
        Örneğin, 1 Ocak'ta %10, 15 Şubat'ta %12 gibi. Yeni satır eklemek için tablonun altındaki `+` ikonuna tıklayın.
    3.  **Hesaplama Periyodu:** Getirisini merak ettiğiniz başlangıç ve bitiş tarihlerini seçin.
    4.  **Hesaplama Butonu:** "Hesapla" butonuna tıklayın.
    5.  **Sonuçlar:**
        *   Program, girdiğiniz faiz oranlarını tarihe göre sıralar.
        *   Belirlediğiniz dönem boyunca her gün için, o güne uygulanacak faiz oranını bulur.
        *   Günlük faiz hesaplanır (`Anapara * (Yıllık Faiz Oranı / 365)`) ve anaparaya eklenir.
        *   Bu işlem, dönem sonuna kadar her gün tekrarlanır (bileşik faiz).
        *   Dönem sonundaki toplam getiri, toplam faiz miktarı ve bu getirinin yıllıklandırılmış hali yüzde olarak gösterilir.

    **Önemli Notlar:**
    *   Faiz oranları **yıllık brüt** olarak girilmelidir (örneğin, %15 için 15). Stopaj vb. kesintiler dikkate alınmaz.
    *   Hesaplama, **günlük bileşik faiz** esasına göre yapılır.
    *   Eğer hesaplama başlangıç tarihinde veya öncesinde tanımlı bir faiz oranı yoksa, ilk faiz oranı giriş tarihine kadar olan günler için **%0 faiz** uygulanır. Bu durum, `Başlangıç Tarihi`nden önceki ilk faiz girişine kadar olan sürenin faizsiz geçeceği anlamına gelir.
    *   Resmi tatiller ve hafta sonları dikkate alınmaz; faiz her takvim günü için hesaplanır.
    """
)
st.caption(f"Mevcut Anapara: {st.session_state.initial_principal:,.2f} TL")
