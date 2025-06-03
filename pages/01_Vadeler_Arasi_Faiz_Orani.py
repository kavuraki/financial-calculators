# -*- coding: utf-8 -*-
import streamlit as st
import math

# -----------------------------------------------------------------------------
# Çekirdek Faiz Hesaplama Fonksiyonu
# -----------------------------------------------------------------------------
def yillik_vadeler_arasi_faiz_hesapla(
    kisa_vade_faiz_orani: float,
    kisa_vade_gun: int,
    uzun_vade_faiz_orani: float,
    uzun_vade_gun: int,
    yil_gun_sayisi: int = 365
) -> tuple[float | None, str | None]:
    """
    İki farklı vade ve bu vadelere ait yıllık faiz oranları verildiğinde,
    bu iki vade arasında kalan dönem için yıllık forward faiz oranını hesaplar.
    """
    hata_mesaji = None
    if not (0 < kisa_vade_gun < uzun_vade_gun):
        hata_mesaji = "Hata: Gün girdileri mantıksız. 'Kısa Vade (Gün)' > 0 ve 'Kısa Vade (Gün)' < 'Uzun Vade (Gün)' olmalıdır."
        return None, hata_mesaji

    if kisa_vade_faiz_orani < -1 or uzun_vade_faiz_orani < -1:
        pass

    kisa_vade_yil = kisa_vade_gun / yil_gun_sayisi
    uzun_vade_yil = uzun_vade_gun / yil_gun_sayisi

    uzun_vade_sonu_deger = 1 + (uzun_vade_faiz_orani * uzun_vade_yil)
    kisa_vade_sonu_deger = 1 + (kisa_vade_faiz_orani * kisa_vade_yil)

    ara_donem_yil = (uzun_vade_gun - kisa_vade_gun) / yil_gun_sayisi

    if ara_donem_yil <= 0:
        hata_mesaji = "Hata: Ara dönem süresi sıfır veya negatif olamaz (bu durum ilk kontrolde yakalanmalıydı)."
        return None, hata_mesaji

    if abs(kisa_vade_sonu_deger) < 1e-9:
        hata_mesaji = "Hata: Kısa vade sonu değer sıfıra çok yakın veya sıfır. Bu, forward faiz hesaplamasında tanımsızlığa yol açar (Örn: Kısa vade faizi %-100 ve vade 1 yıl ise)."
        return None, hata_mesaji

    forward_faizi_yillik = ((uzun_vade_sonu_deger / kisa_vade_sonu_deger) - 1) / ara_donem_yil

    return forward_faizi_yillik, hata_mesaji

# -----------------------------------------------------------------------------
# Streamlit Uygulaması Arayüzü
# -----------------------------------------------------------------------------

st.set_page_config(layout="wide", page_title="Forward Faiz Hesaplayıcı")

st.title("🏦 Vadeler Arası (Forward) Faiz Oranı Hesaplayıcı")
st.markdown("""
Bu uygulama, iki farklı vade için verilen yıllık basit faiz oranlarından yararlanarak,
bu iki vade arasında kalan dönem için yıllık **basit forward faiz oranını** ve ilgili
**günlük bileşik getirileri** hesaplar.
""")

# --- Girdi Alanları ---
st.header("🗓️ Girdi Parametreleri")

yil_gun_sayisi_secenekleri = {
    "365 Gün (Standart)": 365,
    "360 Gün (Bazı Piyasalar)": 360,
    "366 Gün (Artık Yıl)": 366
}
secilen_yil_gun_str = st.selectbox(
    "Yıl İçin Gün Sayısı Konvansiyonu:",
    options=list(yil_gun_sayisi_secenekleri.keys()),
    index=0
)
yil_gun_sayisi = yil_gun_sayisi_secenekleri[secilen_yil_gun_str]
st.info(f"Hesaplamalarda 1 yıl = **{yil_gun_sayisi} gün** olarak alınacaktır.")

st.subheader("1️⃣ Kısa Vade Bilgileri")
kv_faiz_orani_input = st.number_input(
    "Yıllık Basit Faiz Oranı (%) - Kısa Vade",
    min_value=-100.0,
    max_value=1000.0,
    value=48.70,
    step=0.01,
    format="%.2f",
    key="kv_faiz"
)
kv_gun_input = st.number_input(
    "Vade (Gün) - Kısa Vade",
    min_value=1,
    value=30,
    step=1,
    key="kv_gun"
)

st.subheader("2️⃣ Uzun Vade Bilgileri")
uv_faiz_orani_input = st.number_input(
    "Yıllık Basit Faiz Oranı (%) - Uzun Vade",
    min_value=-100.0,
    max_value=1000.0,
    value=46.60,
    step=0.01,
    format="%.2f",
    key="uv_faiz"
)
uv_gun_input = st.number_input(
    "Vade (Gün) - Uzun Vade",
    min_value=1,
    value=93,
    step=1,
    key="uv_gun"
)

kisa_vade_faiz_orani = kv_faiz_orani_input / 100.0
kisa_vade_gun = int(kv_gun_input)
uzun_vade_faiz_orani = uv_faiz_orani_input / 100.0
uzun_vade_gun = int(uv_gun_input)

st.divider()
st.header("📊 Hesaplama Sonuçları")

if st.button("🔄 Hesapla", type="primary", use_container_width=True):
    forward_basit_faiz_yillik, hata = yillik_vadeler_arasi_faiz_hesapla(
        kisa_vade_faiz_orani,
        kisa_vade_gun,
        uzun_vade_faiz_orani,
        uzun_vade_gun,
        yil_gun_sayisi
    )

    if hata:
        st.error(hata)
    elif forward_basit_faiz_yillik is not None:
        ara_donem_gun = uzun_vade_gun - kisa_vade_gun

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"➡️ Forward Dönem ({kisa_vade_gun}. - {uzun_vade_gun}. gün / {ara_donem_gun} gün)")
            st.metric(
                label="Hesaplanan Yıllık Basit Forward Faiz Oranı",
                value=f"{forward_basit_faiz_yillik*100:.4f}%"
            )

        results_container = st.container()
        results_container.subheader("🗓️ Günlük Bileşik Getiri Detayları")

        kisa_donem_toplam_getiri_faktoru = 1 + kisa_vade_faiz_orani * (kisa_vade_gun / yil_gun_sayisi)
        gunluk_bilesik_kisa_str = "Hesaplanamadı"
        if kisa_vade_gun > 0 and kisa_donem_toplam_getiri_faktoru >= 0:
            try:
                gunluk_bilesik_kisa = (kisa_donem_toplam_getiri_faktoru ** (1 / kisa_vade_gun)) - 1
                gunluk_bilesik_kisa_str = f"{gunluk_bilesik_kisa*100:.6f}%"
            except (ValueError, OverflowError):
                gunluk_bilesik_kisa_str = "Matematiksel Hata"

        with results_container:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Kısa Vade ({kisa_vade_gun} gün):**")
                st.info(f"Dönem Sonu Toplam Getiri Faktörü (Basit Faiz): {kisa_donem_toplam_getiri_faktoru:.6f}")
                st.success(f"Günlük Bileşik Getiri Oranı: {gunluk_bilesik_kisa_str}")

        ara_donem_toplam_getiri_faktoru = 1 + forward_basit_faiz_yillik * (ara_donem_gun / yil_gun_sayisi)
        gunluk_bilesik_ara_str = "Hesaplanamadı"
        if ara_donem_gun > 0 and ara_donem_toplam_getiri_faktoru >= 0:
            try:
                gunluk_bilesik_ara = (ara_donem_toplam_getiri_faktoru ** (1 / ara_donem_gun)) - 1
                gunluk_bilesik_ara_str = f"{gunluk_bilesik_ara*100:.6f}%"
            except (ValueError, OverflowError):
                gunluk_bilesik_ara_str = "Matematiksel Hata"

        with results_container:
            with c2:
                st.markdown(f"**Ara Dönem ({ara_donem_gun} gün):**")
                st.info(f"Dönem Sonu Toplam Getiri Faktörü (Basit Faiz): {ara_donem_toplam_getiri_faktoru:.6f}")
                st.success(f"Günlük Bileşik Getiri Oranı: {gunluk_bilesik_ara_str}")

        st.divider()
        st.subheader("🔍 Doğrulama (Günlük Bileşik Getirilerle)")
        valid_calc_kisa = (kisa_vade_gun > 0 and kisa_donem_toplam_getiri_faktoru >= 0 and isinstance(gunluk_bilesik_kisa, float))
        valid_calc_ara = (ara_donem_gun > 0 and ara_donem_toplam_getiri_faktoru >= 0 and isinstance(gunluk_bilesik_ara, float))

        if valid_calc_kisa and valid_calc_ara:
            bilesik_kisa_sonu_deger = (1 + gunluk_bilesik_kisa) ** kisa_vade_gun
            bilesik_uzun_sonu_deger = bilesik_kisa_sonu_deger * ((1 + gunluk_bilesik_ara) ** ara_donem_gun)
            uzun_vade_basit_faiz_sonu_deger = 1 + uzun_vade_faiz_orani * (uzun_vade_gun / yil_gun_sayisi)

            st.write(f"Kısa vade sonu değer (günlük bileşik ile): `{bilesik_kisa_sonu_deger:.8f}` (Basit ile: `{kisa_donem_toplam_getiri_faktoru:.8f}`)")
            st.write(f"Uzun vade sonu değer (günlük bileşikler ile): `{bilesik_uzun_sonu_deger:.8f}`")
            st.write(f"Uzun vade sonu değer (orijinal basit faiz ile): `{uzun_vade_basit_faiz_sonu_deger:.8f}`")

            if math.isclose(bilesik_uzun_sonu_deger, uzun_vade_basit_faiz_sonu_deger, rel_tol=1e-7):
                st.success("✅ Doğrulama başarılı: İki yöntemle hesaplanan uzun vade sonu değerler eşleşiyor.")
            else:
                st.warning(f"⚠️ Doğrulama uyarısı: Değerler arasında küçük bir fark var (Fark: {abs(bilesik_uzun_sonu_deger - uzun_vade_basit_faiz_sonu_deger):.2e}). Bu, yuvarlama farklarından kaynaklanıyor olabilir.")

            st.subheader("📈 Günlük Bileşik Getiri Grafiği")

            days_kv = list(range(kisa_vade_gun + 1))
            returns_kv = [(1 + gunluk_bilesik_kisa)**d for d in days_kv]

            days_fv_plot = list(range(kisa_vade_gun, uzun_vade_gun + 1))
            returns_fv_plot = [returns_kv[-1] * ((1 + gunluk_bilesik_ara)**d) for d in range(ara_donem_gun + 1)]

            days_uzun_vade_plot = list(range(uzun_vade_gun + 1))
            returns_uzun_vade_plot = []
            for d_idx, d_val in enumerate(days_uzun_vade_plot):
                if d_val <= kisa_vade_gun:
                    returns_uzun_vade_plot.append(returns_kv[d_idx])
                else:
                    day_in_forward_period = d_val - kisa_vade_gun
                    returns_uzun_vade_plot.append(
                        returns_kv[-1] * ((1 + gunluk_bilesik_ara)**day_in_forward_period)
                    )

            # Grafik kaldırıldı.
        else:
            st.warning("Doğrulama için gerekli günlük bileşik getirilerden biri veya birkaçı hesaplanamadı.")
    else:
        st.error("Beklenmedik bir hata oluştu, forward faiz oranı hesaplanamadı.")
else:
    st.info("Hesaplama yapmak için lütfen sol paneldeki 'Hesapla' butonuna tıklayın.")

# Sidebar kaldırıldı.