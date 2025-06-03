import streamlit as st

# Set the page configuration
st.set_page_config(
    page_title="Finansal Hesaplama Araçları",
    layout="wide"
)

# Main title for the application
st.title("Finansal Hesaplama Araçları")

# Header for the dashboard
st.header("Hesap Makinesi Paneli")

st.markdown("""
Finansal Hesaplama Araçları uygulamasına hoş geldiniz!

Bu platform, çeşitli finansal planlama ve analiz görevlerinde size yardımcı olmak için tasarlanmış bir dizi hesap makinesi sunar.
Bileşik faizin gücünü anlamak, kredi geri ödemelerini tahmin etmek, emeklilik için plan yapmak veya forward faiz oranlarını analiz etmek istiyorsanız, bu araçlar size yardımcı olmak için buradadır.

Başlamak için soldaki kenar çubuğunu kullanarak istediğiniz hesap makinesine gidin.
Her hesap makinesi, belirli bir finansal senaryoya göre uyarlanmıştır ve net girdiler ile anlayışlı sonuçlar sunar.
""")
st.markdown("---")

st.info("💡 **İpucu:** Farklı finansal hesap makinelerini keşfetmek için kenar çubuğunu kullanın.")

st.markdown("""
Hem güçlü hem de kullanımı kolay araçlar sunmayı amaçlıyoruz. Herhangi bir geri bildiriminiz veya öneriniz varsa, lütfen bize bildirin!
""")
