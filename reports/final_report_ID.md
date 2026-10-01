# Analisis Pelanggan & Market Basket Instacart
### Laporan Akhir

**Peran:** Data Analyst · **Dataset:** Instacart Online Grocery Shopping Dataset 2017

**Cakupan:** 206.209 pelanggan · 3.421.083 pesanan · 33.819.106 item terbeli · 49.688 produk

---

## 1. Ringkasan Eksekutif

Data transaksi Instacart menggambarkan sebuah **bisnis replenishment (pembelian ulang), bukan
bisnis discovery (penemuan produk baru)**. **59,0% dari setiap item yang terjual adalah barang
yang sudah pernah dibeli pelanggan tersebut**, dan angka tunggal itulah yang menentukan di mana
peluang komersialnya berada.

Enam temuan menjadi tulang punggung analisis ini:

1. **Kebiasaan membeli ulang terbentuk antara pesanan ke-2 dan ke-6 pelanggan.** Reorder rate
   naik dari 27,2% ke 54,1% di rentang itu, lalu mendatar. Biaya retensi yang dikeluarkan
   setelah pesanan ke-10 sebagian besar terbuang pada pelanggan yang memang sudah bertahan.
2. **Frekuensi pesanan dan ukuran basket tidak berhubungan secara statistik** (Spearman
   ρ = 0,06). Keduanya adalah dua tuas pertumbuhan yang terpisah, dan memperlakukan
   "engagement" sebagai satu angka justru mencampuradukkan keduanya.
3. **Pelanggan berjalan pada ritme mingguan.** 50,9% pesanan ulang datang dalam 7 hari, dengan
   lonjakan jelas tepat di hari ke-7 — titik pemicu yang tidak perlu dikarang sendiri oleh bisnis.
4. **Produce menarik traffic; dairy yang membuat pelanggan kembali.** Produce menyumbang 29,2%
   unit dan hadir di 74,9% basket, tetapi dairy & eggs punya reorder rate tertinggi di antara
   seluruh departemen (67,0%).
5. **Reorder rate adalah alat ukur kecepatan konsumsi, bukan skor kepuasan.** Kategori
   menjelaskan 56,3% variansi reorder rate sebuah produk. Angka 47,7% pada minyak zaitun itu
   sehat; angka 47,7% pada susu justru mengkhawatirkan.
6. **Sinyal cross-sell terbaik bersifat kuliner, dan produk terlaris justru tidak berguna
   sebagai rekomendasi.** Bawang putih↔bawang bombay (lift 5,64) dan pasta↔saus pasta
   (lift 4,41) nyata; sementara pisang ada di 14,7% basket sehingga tidak memprediksi apa pun —
   padahal pisang menjadi konsekuen dari 21,5% seluruh rule yang ditemukan.

Enam rekomendasi menyusul di §11, masing-masing terikat pada bukti di atas. Yang bernilai
paling tinggi adalah **langganan replenishment yang dibibitkan dari klaster susu dan yogurt**,
di mana perilakunya sudah ada dengan reorder rate 84–86% dan produk hanya diminta berhenti
membuat pelanggan mengetik ulang.

**Yang tidak bisa dijawab dataset ini:** tidak ada harga, margin, tanggal, maupun demografi.
Tidak ada satu pun angka pendapatan di laporan ini, dan musiman (seasonality) tidak dapat diukur.

---

## 2. Permasalahan Bisnis

> *Bagaimana perilaku pembelian pelanggan Instacart, produk apa yang paling penting bagi
> mereka, dan produk apa yang sebaiknya dipasarkan atau direkomendasikan bersama?*

Dipecah menjadi pertanyaan yang harus dijawab analisis ini:

| # | Pertanyaan | Dijawab di |
|---|---|---|
| 1 | Siapa pelanggannya dan bagaimana mereka berbelanja? | §6 |
| 2 | Produk dan kategori apa yang paling penting? | §7 |
| 3 | Kapan pelanggan berbelanja? | §5 |
| 4 | Apa yang mendorong pembelian ulang? | §8 |
| 5 | Produk apa yang dibeli bersamaan? | §9 |
| 6 | Peluang bisnis apa yang mengikutinya? | §10–11 |

---

## 3. Dataset

Enam tabel dengan skema berbentuk bintang, dan satu tabel fakta besar yang terbagi ke dua berkas.

| Tabel | Baris | Granularitas | Peran |
|---|---:|---|---|
| `orders` | 3.421.083 | satu pesanan | header fakta — pelanggan, urutan, hari, jam, interval |
| `order_products__prior` | 32.434.489 | produk × pesanan | isi basket, seluruh riwayat |
| `order_products__train` | 1.384.617 | produk × pesanan | isi basket, pesanan terakhir dari 131.209 pelanggan |
| `products` | 49.688 | satu produk | dimensi; membawa kunci aisle sekaligus department |
| `aisles` | 134 | satu aisle | dimensi |
| `departments` | 21 | satu department | dimensi |

```
 departments (21) ──┐
                    ├──> products (49.688) ──> order_products (33,8 juta baris)
 aisles (134) ──────┘                               ^
                                                    │
                            orders (3,42 juta) ─────┘
                              user_id  (tidak ada tabel pelanggan)
```

**Dua fakta struktural membentuk keseluruhan proyek ini.**

*Tidak ada tabel pelanggan.* Setiap atribut pelanggan dalam laporan ini — jumlah pesanan,
rata-rata basket, reorder rate, interval, segmen — diturunkan dari riwayat pesanan.
Segmentasi demografis sejak awal bukan pilihan yang tersedia.

*75.000 pesanan tidak memiliki isi.* Pesanan `test` ditahan pada rilis Kaggle aslinya. Pesanan
ini dikeluarkan dari seluruh analisis tingkat item dan tetap dipakai untuk analisis waktu
pesanan, karena field waktunya valid. Setiap tabel dalam laporan ini menyebut basisnya:

- **seluruh pesanan (3.421.083)** — waktu, frekuensi, interval
- **pesanan yang isinya diketahui (3.346.083)** — produk, kategori, basket, reorder rate

---

## 4. Persiapan Data

### 4.1 Kualitas data

Dataset ini luar biasa bersih: **nol foreign key yatim, nol baris duplikat, dan nol kode tidak
valid**, serta kunci komposit `(order_id, product_id)` unik di kedua berkas basket. **Tidak ada
satu baris pun yang dihapus dan tidak ada satu nilai pun yang diimputasi di seluruh proyek ini.**

Yang dibutuhkan adalah interpretasi, bukan perbaikan. Empat field mudah disalahbaca:

| # | Persoalan | Keputusan | Alasan |
|---|---|---|---|
| 1 | 206.209 null di `days_since_prior_order` | dipertahankan sebagai null + flag `is_first_order` | Setiap null berada tepat di `order_number = 1`, dan jumlahnya sama persis dengan jumlah pelanggan. Null di sini berarti "belum ada pesanan sebelumnya". Mengisinya dengan 0 akan mengarang 206.209 pembelian ulang di hari yang sama. |
| 2 | `days_since_prior_order` dipotong di 30 (10,8% pesanan) | diberi flag `dspo_is_capped`; interval dilaporkan dua cara | 369.323 pesanan berada tepat di 30 berbanding 18.418 di 29 — tebing 20× yang tidak dihasilkan perilaku apa pun. "30" berarti "paling tidak 30 hari". |
| 3 | 99 nama produk dipakai lebih dari satu `product_id` | ditambahkan `product_uid` yang menyatukan id bernama sama di aisle sama | 'BBQ Sauce' dan 'Bbq Sauce' adalah satu barang yang terdaftar dua kali. Saat terpisah peringkatnya #12.002; setelah disatukan #9.842. Hanya 0,23% katalog yang terdampak, dan `product_id` sama sekali tidak diubah. |
| 4 | Kategori placeholder `missing` / `other` (1.258 produk) | diberi flag `is_placeholder`; tetap dihitung di total, dikeluarkan dari ranking | Kantong "tidak diketahui" tidak boleh memenangkan ranking kategori teratas. |

Juga dibawa ke depan: `order_number` dipotong di 100 (1.374 pelanggan berada di angka itu), dan
`order_dow` **tidak memiliki pemetaan hari yang terdokumentasi** — nama hari dalam laporan ini
adalah asumsi yang dinyatakan terbuka, dan tidak ada satu kesimpulan pun yang bergantung padanya.

**Outlier diperiksa dan dipertahankan.** Basket terbesar berisi 145 item dan pelanggan tersibuk
punya 100 pesanan. Keduanya masuk akal untuk belanja bahan pokok, dan membuangnya justru akan
menghapus persis perilaku bernilai tinggi yang ingin dijelaskan proyek ini.

### 4.2 Integrasi

Rantai yang disyaratkan — Customer → Order → Order Product → Product → Aisle → Department —
dibangun dengan satu aturan utama: **agregasi dulu, baru join.** Menggabungkan 33,8 juta baris
basket ke 3,42 juta pesanan akan memekarkan tabel pesanan menjadi 33,8 juta baris dan diam-diam
membuat setiap rata-rata tingkat pesanan tertimbang oleh ukuran basket. Karena itu ukuran basket
diagregasi dulu ke granularitas pesanan, baru di-join kembali.

**Setiap join mengubah jumlah baris tepat nol**, dan itulah pengujian bahwa join many-to-one di
atas primary key sudah benar. Left join (bukan inner) mempertahankan 75.000 pesanan test dengan
basket size null alih-alih membuangnya.

---

## 5. Analisis Eksploratif — Kapan Pelanggan Berbelanja

**Jam.** 64,9% dari seluruh pesanan dibuat antara pukul 09.00 dan 16.00, memuncak pada pukul
10.00 (288.418 pesanan). Dini hari (00.00–05.00) hanya 1,8%. Namun **jam tersibuk bukanlah jam
dengan basket terbesar**: pukul 21.00–23.00 hanya menyumbang 5,3% pesanan tetapi memiliki basket
terbesar sepanjang hari (10,7–11,0 item dibanding 10,1 secara keseluruhan).

**Hari.** Hari 0 dan 1 menyumbang 34,7% dari satu minggu (600.905 + 587.478 pesanan); hari
tersepi menyumbang 12,5%. Rasio puncak terhadap lembah hanya 1,41×. Yang penting, **kedua hari
puncak itu berbeda bentuknya** — hari 0 memuncak pukul 13.00–15.00 dengan basket 11,2 item,
hari 1 memuncak pukul 09.00–11.00 dengan 10,2 item. Satu kampanye akhir pekan yang dikirim pada
satu waktu akan melewatkan salah satunya.

**Interval.** 50,9% pesanan ulang datang dalam 7 hari, dan hari ke-7 menjadi lonjakan yang
terlihat jelas (10,0% pesanan ulang, berbanding 7,5% di hari ke-6 dan 5,7% di hari ke-8), dengan
gundukan sekunder di hari 14, 21, dan 30. **Pelanggan menjalankan belanja mingguan.**

Interval juga memprediksi isi basket: reorder rate mencapai **65,8%** untuk pesanan dalam 3 hari
dan **48,0%** untuk pesanan setelah 25+ hari. Pelanggan yang kembali setelah seminggu
menginginkan daftar biasanya; yang kembali setelah sebulan sedang membangun ulang kebiasaannya.

**Posisi di keranjang.** Reorder rate turun dari **67,9% di posisi keranjang ke-1** menjadi
51,0% di posisi ke-15. Pelanggan memasukkan kebiasaannya lebih dulu, baru menjelajah — dan ini
adalah instruksi langsung tentang di bagian mana sesi belanja seharusnya menempatkan discovery.

---

## 6. Analisis Pelanggan

**Frekuensi.** Median 10 pesanan per pelanggan, rata-rata 16,6 (skew 2,4). Konsentrasinya nyata
tetapi moderat: 10% pelanggan teratas membeli **35,1%** item, 20% teratas membeli **53,7%**.
Ini **bukan** bisnis 80/20 — separuh pelanggan terbawah masih menyumbang 17,8% volume.

**Hasil negatif yang penting.** Frekuensi pesanan dan ukuran basket **tidak berkorelasi**
(ρ = 0,06). Yang justru bergerak seiring jumlah pesanan adalah reorder rate (ρ = 0,73) dan,
secara negatif, interval (ρ = −0,60). Di sepanjang pita jumlah pesanan, ukuran basket hanya
bergerak 9,6 → 10,4 item sementara reorder rate bergerak **23,0% → 73,7%** dan interval turun
**20,3 → 5,1 hari**.

> **Loyalitas di sini berarti frekuensi dan pengulangan, bukan ukuran basket.** Promosi
> "belanja $10 lagi" menekan tuas yang tidak bergerak.

**Segmentasi.** K-Means atas tiga dimensi yang diminta brief (jumlah pesanan — ditransformasi
log karena skew-nya 2,4 — rata-rata basket, reorder rate).

*Disampaikan apa adanya:* skor silhouette memuncak di k = 2 (0,365) dan tidak pernah melewati
0,37, sementara kurva elbow tidak memiliki patahan tajam. **Basis pelanggan ini adalah
kontinum, bukan sekumpulan suku alami.** k = 4 dipilih karena memisahkan dua tuas independen
tadi menjadi segmen yang bisa diperlakukan berbeda — sebuah partisi manajerial, bukan penemuan.

| Segmen | Pelanggan | % item | Pesanan | Basket | Reorder | Interval |
|---|---:|---:|---:|---:|---:|---:|
| **Loyal Regulars** | 44.475 (21,6%) | **53,4%** | 40,6 | 10,1 | **69,0%** | 8,8 hari |
| **Big-Basket Stockers** | 33.020 (16,0%) | 20,6% | 10,6 | **19,4** | 46,2% | 16,9 hari |
| **Steady Small-Basket** | 62.996 (30,5%) | 17,1% | 12,9 | **7,0** | 49,3% | 15,6 hari |
| **Occasional / At-Risk** | 65.718 (31,9%) | 8,9% | 5,7 | 8,0 | **22,3%** | **19,1 hari** |

Satu dari lima segmen membeli lebih dari separuh volume. Sepertiga basis pelanggan menghasilkan
seperdua belasnya. Dua segmen tengah memiliki jumlah pesanan hampir sama dengan basket berbeda
2,8× — keduanya butuh intervensi yang berlawanan.

---

## 7. Analisis Produk & Kategori

**Produk teratas.** Pisang memimpin dengan 491.291 unit yang dibeli 76.125 pelanggan (**36,9%
dari seluruh pelanggan**), disusul pisang organik (394.930). Sembilan dari sepuluh teratas
adalah produce segar. Papan peringkat volume dan papan peringkat reorder **hampir identik** —
produk-produk ini besar karena orang yang sama membelinya berulang kali, bukan karena banyak
orang mencobanya sekali.

**Reorder rate tertinggi** (minimum 2.000 pembelian, karena rate atas 12 pembelian hanyalah
derau): sembilan dari sepuluh teratas adalah **varian susu**, dari 86,1% hingga 83,9%, dengan
pisang sebagai satu-satunya entri non-dairy. Ini adalah produk yang **habis dipakai**, bukan
produk yang **dipilih**.

**Konsentrasi.** 100 produk teratas menyumbang 23,1% unit dan 1% teratas menyumbang 42,7% —
tetapi untuk mencapai 80% volume tetap dibutuhkan **4.548 produk**. Ini bukan bisnis segelintir
SKU unggulan, dan juga bukan long tail yang datar.

**Volume vs loyalitas.** Membelah 8.563 produk dengan ≥500 pembelian pada median kelompok
tersebut (1.287 unit, reorder rate 54,6%):

| Kuadran | Produk | Unit | Porsi | Contoh | Strategi |
|---|---:|---:|---:|---|---|
| **Core staples** | 2.537 | 20,4 jt | **67,5%** | Pisang, baby spinach, susu full cream | Jangan pernah kosong stok |
| **Traffic drivers** | 1.745 | 6,4 jt | 21,1% | Minyak zaitun, daun bawang, jahe | Akuisisi, pengisi basket |
| **Loyal niche** | 1.746 | 1,4 jt | 4,7% | Sereal tertentu, granola bar | Rekomendasi terpersonalisasi |
| **Long tail** | 2.535 | 2,0 jt | 6,6% | Piring kertas, keju spesialis | Kelengkapan ragam |

**Kategori.** Produce menyumbang 29,2% unit dan menjangkau **74,9% basket**; dairy & eggs
menyumbang 16,7% unit tetapi memiliki **reorder rate tertinggi di antara seluruh departemen,
67,0%**. Keduanya bersama mencakup 45,9% dari semua yang terjual. Di sisi terbawah, personal
care (32,2%) dan pantry (34,7%) paling jarang dibeli ulang.

Aisle paling kebiasaan: **milk, 78,2%**. Paling jarang: **spices & seasonings, 15,3%**, disusul
food storage (25,5%), cleaning products (29,0%), dan baking ingredients (30,5%).

> Setiap kategori ber-reorder rendah dalam daftar itu adalah kategori **berkonsumsi lambat**.
> Satu toples jintan bertahan setahun. Ini soal ritme konsumsi, bukan ketidakpuasan.

---

## 8. Analisis Reorder

**59,0%** dari seluruh baris basket adalah pembelian ulang; **62,9%** setelah pesanan pertama —
yang secara definisi tidak mungkin memuat pembelian ulang — dikeluarkan.

**Kurva kebiasaan.** Reorder rate menurut pesanan ke-n seorang pelanggan:

| Pesanan ke- | 1 | 2 | 3 | 4 | 5 | 6 | 10 | 20 | 50 |
|---|---|---|---|---|---|---|---|---|---|
| Reorder rate | 0% | 27,2% | 38,6% | 45,4% | 50,3% | **54,1%** | 63,4% | 73,6% | 81,9% |

Kurva ini naik **27 poin persentase antara pesanan ke-2 dan ke-6** lalu mendatar. **Itulah
jendela pembentukan kebiasaan**, dan itu temuan waktu yang paling bisa ditindaklanjuti dalam
proyek ini.

Menurut masa pakai pelanggan, rentangnya 24,0% (3–4 pesanan seumur hidup) sampai **75,2%**
(51–100). Pelanggan berat juga **lebih banyak** menjelajah secara absolut — 169,8 produk
berbeda berbanding 26,5 — sehingga pengulangan dan keluasan tumbuh bersama, bukan saling
menukar.

**Reorder rate harus dibandingkan di dalam kategorinya sendiri.** Dekomposisi variansi
menunjukkan **aisle menjelaskan 56,3%** variansi reorder rate sebuah produk, dan department
40,5%. Sisa ~44% itulah tempat preferensi produk yang sesungguhnya berada. Minyak zaitun di
47,7% berkinerja baik untuk pantry (rata-rata 32,9%); susu di 60% justru berkinerja buruk untuk
dairy (rata-rata 61,9%).

---

## 9. Market Basket Analysis

**Metode.** FP-Growth (pohon prefiks, bukan pemindaian berulang ala Apriori) atas sampel acak
tetap sebanyak **600.000 basket** (seed 42), pada dua tingkat: **300 produk teratas** (35,6%
unit; 65,4% basket memuat ≥2 di antaranya) dan **seluruh 134 aisle**. Basket yang tidak memuat
satu pun item dalam cakupan tetap dihitung di penyebut, sehingga support tidak pernah
digelembungkan dengan mengecilkan semesta.

**Ambang batas, dijustifikasi dari datanya.** Minimum support 0,001 (≥600 dari 600.000 basket),
minimum confidence 0,05, minimum lift 1,0. Pada support 0,005 hanya 95 rule yang bertahan dan
semuanya pasangan pisang; pada 0,0005 keluarannya terlalu jarang untuk dijadikan dasar
merchandising. Confidence sengaja dibuat rendah — dengan median basket 8 item dari 49.573
produk, probabilitas bersyarat 5% sudah merupakan sinyal kuat, dan angka 50% ala buku teks
hanya akan mengembalikan tautologi. **Lift yang melakukan perankingan.** Hasil: **3.048 rule
produk** dan **3.692 rule aisle** (brief meminta minimum 10).

### Tabel rule yang disyaratkan

| Antecedent | Consequent | Support | Conf. | Lift |
|---|---|---:|---:|---:|
| Total 2% Greek Yogurt Blueberry | Total 2% Strawberry + Total 2% Peach | 0,12% | 18,6% | **75,58** |
| Icelandic Skyr Blueberry | Non Fat Raspberry Yogurt | 0,22% | 38,0% | **75,61** |
| Total 2% Strawberry + Peach | Total 2% Blueberry | 0,12% | 61,6% | 68,12 |
| Sparkling Lemon + Grapefruit Water | Lime Sparkling Water | 0,14% | 47,0% | 32,36 |
| Organic Garlic | Organic Yellow Onion | — | — | **5,64** (berpasangan) |
| dry pasta | pasta sauce | 1,95% | 27,4% | **4,41** |
| pasta sauce | dry pasta | 1,95% | 31,4% | **4,41** |
| Limes | Large Lemon | — | — | **4,08** (berpasangan) |
| canned meals/beans | canned jarred vegetables | 1,83% | 26,3% | 3,55 |
| Organic Cucumber | Organic Grape Tomatoes | — | — | 3,77 (berpasangan) |
| fresh herbs | fresh vegetables | 7,96% | **84,6%** | 1,90 |
| Organic Hass Avocado | Bag of Organic Bananas | 1,94% | 29,1% | 2,45 |

### Interpretasi bisnis — tiga pola yang berbeda

**Pola 1 — Ragam rasa dalam satu lini merek (lift 30–76).** Asosiasi terkuat dalam dataset ini
terjadi antar *rasa berbeda dari lini yogurt yang sama* (lift sampai 75,6, confidence sampai
61,6%), dengan air berkarbonasi menunjukkan bentuk serupa. **Ini bukan peluang cross-sell** —
pelanggan sudah memilih mereknya dan sedang menyusun paket campuran di dalam keputusan yang
sudah diambil. Nilainya ada di tempat lain: *bundel multipack* (mengubah empat baris pesanan
menjadi satu pengambilan), *perlindungan ragam* (menghapus satu rasa akan merusak penjualan
rasa lain), dan *logika substitusi* (kalau blueberry habis, pengganti yang tepat adalah
strawberry dari lini yang sama, bukan blueberry merek lain).

**Pola 2 — Pelengkap resep (lift 3–6).** Inilah rule cross-sell yang sesungguhnya, ditemukan di
antara produk yang masing-masing laris sehingga kelangkaan tidak bisa menjelaskan asosiasinya:
bawang putih↔bawang bombay **5,64**, jeruk nipis↔lemon **4,08**, timun↔tomat anggur **3,77**,
lemon↔alpukat 3,62. Niat pelanggan — *memasak satu hidangan* — baru sebagian terungkap lewat
item pertama, dan justru itulah yang membuat ajakan terasa berguna alih-alih mengganggu.

**Pola 3 — Kedekatan kategori (support tinggi).** Rule aisle jauh lebih kokoh, berlaku di 1–2%
dari *seluruh* basket: **dry pasta ↔ pasta sauce (lift 4,41)**, canned meals ↔ canned vegetables
(3,55), dan **fresh herbs → fresh vegetables dengan confidence 84,6%** — confidence
antecedent-tunggal tertinggi yang ditemukan di tingkat mana pun. Rule semacam ini
mengidentifikasi **misi belanja**, bukan sekadar afinitas produk, sehingga lebih tepat dijadikan
dasar merchandising, penjadwalan kampanye, dan perancangan jalur pengambilan barang di gudang.

**Temuan negatifnya penting secara komersial.** Pisang ada di 14,7% basket, sehingga muncul
bersama apa pun dan tidak memprediksi apa pun — namun pisang menjadi konsekuen dari **21,5%
seluruh rule yang ditemukan**. Sistem rekomendasi yang diranking berdasarkan confidence akan
merekomendasikan hampir tidak ada hal lain.

### Keterbatasan

1. Asosiasi bukan kausalitas — bawang putih dan bawang bombay muncul bersama karena keduanya ada
   di resep yang sama.
2. Support bersifat relatif terhadap sampel 600.000 basket dan cakupan 300 produk teratas;
   *perankingannya* stabil, angka support absolutnya bergantung cakupan.
3. **Tidak ada data harga maupun margin**, sehingga setiap rekomendasi bundel bersyarat pada
   pemeriksaan margin.
4. Tidak ada tanggal, sehingga musiman tidak terlihat dan akan terata-ratakan ke angka tahunan.

---

## 10. Temuan Utama

Masing-masing disusun sebagai **Temuan → Bukti → Makna bisnis**.

**Temuan 1 — Ini bisnis replenishment.**
*Bukti:* 59,0% dari 33,8 juta item yang terjual adalah pembelian ulang (62,9% jika pesanan
pertama dikeluarkan), naik hingga 81,9% pada pesanan ke-50 seorang pelanggan.
*Makna bisnis:* persoalan produk yang utama adalah membuat daftar belanja yang sudah dikenal
menjadi mudah, bukan memunculkan hal baru. Fitur discovery justru bersaing dengan tugas yang
membuat kebanyakan pelanggan datang.

**Temuan 2 — Kebiasaan terbentuk antara pesanan ke-2 dan ke-6.**
*Bukti:* reorder rate naik 27,2% → 54,1% di rentang itu lalu mendatar (63,4% di pesanan ke-10,
81,9% di pesanan ke-50). Menurut masa pakai: 24,0% untuk pelanggan 3–4 pesanan berbanding 75,2%
untuk 51–100.
*Makna bisnis:* di sinilah belanja retensi punya daya ungkit. Pelanggan yang mencapai pesanan
keenam sudah berperilaku seperti pelanggan yang bertahan; yang mandek di tiga, belum. Setelah
pesanan ke-10 pengeluaran sebagian besar mubazir.

**Temuan 3 — Frekuensi dan ukuran basket adalah tuas yang terpisah.**
*Bukti:* Spearman ρ = 0,06 antara jumlah pesanan dan rata-rata basket; sepanjang pita jumlah
pesanan, basket hanya bergerak 9,6 → 10,4 item sementara reorder rate bergerak 23,0% → 73,7%.
*Makna bisnis:* satu "skor engagement" mencampur dua perilaku yang tidak berhubungan. Pelanggan
Steady Small-Basket (7,0 item, 12,9 pesanan) butuh pembesaran basket; Big-Basket Stockers
(19,4 item, 10,6 pesanan) butuh frekuensi. Satu kampanye tidak bisa melakukan keduanya.

**Temuan 4 — Pelanggan berjalan pada ritme mingguan.**
*Bukti:* 50,9% pesanan ulang dalam 7 hari; lonjakan tepat di hari ke-7 (10,0% berbanding 7,5%
di hari ke-6 dan 5,7% di hari ke-8); gundukan sekunder di hari 14, 21, 30.
*Makna bisnis:* pemicu pengingat tidak perlu dikarang atau ditebak lewat A/B — basis pelanggan
sudah memilihnya sendiri. Penyimpangan dari interval khas seorang pelanggan merupakan sinyal
churn yang lebih baik dibanding ambang tetap mana pun.

**Temuan 5 — Produce menarik traffic; dairy mendatangkan kembali.**
*Bukti:* produce = 29,2% unit dan penetrasi basket 74,9%, reorder rate 65,1%; dairy & eggs =
16,7% unit tetapi reorder rate tertinggi di antara seluruh departemen, 67,0%, dipimpin susu di
78,2%.
*Makna bisnis:* dua peran berbeda yang membenarkan dua investasi berbeda. Kualitas dan
ketersediaan produce mendorong akuisisi dan jangkauan basket; keandalan dairy mendorong frekuensi.

**Temuan 6 — Reorder rate mengukur ritme konsumsi, bukan kepuasan.**
*Bukti:* aisle menjelaskan 56,3% variansi reorder rate produk (department 40,5%). Aisle dengan
reorder terendah — rempah 15,3%, food storage 25,5%, baking 30,5% — semuanya kategori
berkonsumsi lambat.
*Makna bisnis:* jangan pernah menilai produk terhadap angka 59% keseluruhan. Bandingkan di
dalam kategorinya, atau setiap barang pantry akan tampak gagal dan setiap susu akan tampak sukses.

**Temuan 7 — Sinyal cross-sell yang nyata bersifat kuliner, dan produk terlaris tidak berguna
untuk itu.**
*Bukti:* bawang putih↔bawang bombay lift 5,64, pasta↔saus pasta 4,41, jeruk nipis↔lemon 4,08;
sementara pisang ada di 14,7% basket dan menjadi konsekuen 21,5% seluruh rule.
*Makna bisnis:* bundel berbentuk resep dan ajakan melengkapi basket didukung bukti. Sistem
rekomendasi yang diranking berdasarkan confidence tidak — sistem itu akan merekomendasikan
pisang kepada semua orang.

**Temuan 8 — Pesanan kecil membebani operasional secara tidak proporsional.**
*Bukti:* 17,1% pesanan berisi 3 item atau kurang tetapi hanya menyumbang 3,5% unit; 4,9%
berisi satu item. Pesanan mungil ini justru punya reorder rate **tertinggi** (65,0%) — mereka
adalah pembelian susulan barang penting yang terlupa.
*Makna bisnis:* aturan minimum pembelian justru akan menekan sinyal kebiasaan. Pembesaran
basket — mengingatkan pelanggan pada barang langganannya sendiri saat checkout — menjawab sisi
ekonominya tanpa menghukum perilakunya.

---

## 11. Rekomendasi Bisnis

Setiap rekomendasi menyebutkan bukti yang mendasarinya dan cara mengukurnya.

### R1 — Luncurkan langganan replenishment, dibibitkan dari klaster susu & yogurt

**Bukti.** Sembilan reorder rate tertinggi di katalog (≥2.000 pembelian) semuanya varian susu,
83,9–86,1%. Milk adalah aisle paling kebiasaan di 78,2%; dairy & eggs departemen paling
kebiasaan di 67,0%. 50,9% pesanan ulang datang dalam 7 hari.
**Aksi.** Tawarkan penambahan otomatis mingguan atau dua mingguan untuk 3–5 produk langganan
teratas pelanggan, dengan default mengikuti interval yang teramati pada pelanggan itu sendiri,
bukan jadwal tetap, serta tombol lewati sekali sentuh.
**Alasan efektif.** Perilakunya sudah ada di angka 84%+; produk hanya menghapus pekerjaan
mengetik ulang. Pelanggan tidak diminta mengubah apa pun.
**Ukuran.** Porsi pesanan yang memuat item berlangganan; variansi interval sebelum vs sesudah;
churn pelanggan berlangganan dibanding kelompok kontrol yang dipadankan.
**Risiko.** Kelebihan kiriman merusak kepercayaan dengan cepat. Buat default mudah dilewati, dan
jangan pernah menambahkan otomatis kategori berkonsumsi lambat (apa pun di bawah ~40% reorder
rate — pantry, rempah, pembersih).

### R2 — Pusatkan belanja retensi pada pesanan ke-2 hingga ke-6

**Bukti.** Reorder rate naik 27,2% → 54,1% antara pesanan ke-2 dan ke-6 lalu mendatar. Pelanggan
Occasional / At-Risk (31,9% basis, 8,9% item) rata-rata 5,7 pesanan dengan reorder rate 22,3% —
mereka mandek persis di jendela ini.
**Aksi.** Rangkaian onboarding tetap sepanjang enam pesanan pertama pelanggan baru: ajakan
membeli ulang dari isi basket pertamanya sendiri, pengingat yang diselaraskan dengan interval
yang mulai terbentuk, dan insentif dipadatkan di pesanan ke-2 sampai ke-4 alih-alih disebar rata.
**Alasan efektif.** Menyasar satu-satunya bagian siklus hidup di mana kurvanya curam.
Pengeluaran setelah pesanan ke-10 sebagian besar jatuh ke pelanggan yang memang akan bertahan.
**Ukuran.** Porsi pelanggan baru yang mencapai pesanan ke-6 dalam jendela waktu tetap; reorder
rate di pesanan ke-6 dibanding kontrol.
**Risiko.** Dataset ini tidak punya tanggal, sehingga "dalam 90 hari" tidak dapat divalidasi di
sini — jendelanya perlu dikalibrasi dengan data live sebelum diluncurkan.

### R3 — Perlakukan dua segmen tengah sebagai dua masalah berbeda

**Bukti.** Frekuensi pesanan dan ukuran basket tidak berkorelasi (ρ = 0,06). Steady
Small-Basket: 62.996 pelanggan, 7,0 item, 12,9 pesanan, interval 15,6 hari. Big-Basket Stockers:
33.020 pelanggan, 19,4 item, 10,6 pesanan, interval 16,9 hari.
**Aksi.** Untuk Small-Basket, pembesaran basket — ajakan melengkapi basket yang diambil dari
pasangan resep di R4, serta pengingat barang langganannya sendiri saat checkout. Untuk Stockers,
frekuensi — pengingat replenishment di sekitar hari ke-14, bukan keranjang yang lebih besar.
**Alasan efektif.** Masing-masing menekan tuas yang memang bisa digerakkan untuk kelompok itu.
Satu kampanye "engagement" akan menekan tuas yang salah bagi separuhnya.
**Ukuran.** Ukuran basket untuk Small-Basket; interval pesanan untuk Stockers. Tiap segmen hanya
dinilai dengan metriknya sendiri.
**Risiko.** Segmen adalah partisi atas kontinum (silhouette ≤ 0,37), sehingga batasnya akan
bergeser saat dijalankan ulang. Tetapkan berdasarkan perilaku terkini, skor ulang secara
berkala, dan jangan pernah menampilkan nama segmen kepada pelanggan.

### R4 — Bangun ajakan melengkapi basket di atas pasangan resep, bukan popularitas

**Bukti.** Di antara produk terlaris: bawang putih↔bawang bombay lift 5,64, jeruk nipis↔lemon
4,08, timun↔tomat anggur 3,77, lemon↔alpukat 3,62. Di tingkat aisle: pasta↔saus pasta lift 4,41
pada 1,95% basket. Sebaliknya: pisang menjadi konsekuen 21,5% seluruh rule tanpa menambah
informasi apa pun.
**Aksi.** Luncurkan tiga paket berbukti — bumbu dasar (bawang putih, bawang bombay), paket salad
(timun, tomat, lemon), malam pasta (pasta kering, saus, parmesan) — dan ajakan melengkapi yang
dipicu oleh *celah*: bawang putih di basket tanpa bawang bombay. Keluarkan secara eksplisit ~20
produk dengan penetrasi basket tertinggi dari kelayakan rekomendasi.
**Alasan efektif.** Menyasar niat yang baru sebagian terungkap lewat item pertama, dan itulah
yang membuat ajakannya berguna alih-alih mengganggu. Mengeluarkan pisang menghilangkan sumber
rekomendasi tak berguna yang terbesar.
**Ukuran.** Tingkat penerimaan ajakan, dan tambahan unit dari *konsekuennya* — bukan total
ukuran basket, yang bergeser karena sebab-sebab lain.
**Risiko.** **Tidak ada data margin dalam dataset ini.** Setiap bundel wajib lolos pemeriksaan
margin sebelum diluncurkan; pasangan ber-lift tinggi yang keduanya bermargin tipis tidak bernilai
secara komersial.

### R5 — Tetapkan tingkat layanan per kuadran, dan bandingkan reorder rate di dalam kategori

**Bukti.** 2.537 core staples (5% produk yang pernah terbeli) menyumbang 67,5% unit pada
kelompok ≥500 pembelian dengan rata-rata reorder rate 64,8%. Aisle menjelaskan 56,3% variansi
reorder rate produk. Rempah ber-reorder 15,3%, susu 78,2% — dan keduanya sehat.
**Aksi.** Bertingkatkan ketersediaan menurut kuadran: core staples mendapat jaminan tingkat
layanan tertinggi dan logika substitusi; traffic drivers dikelola untuk keluasan; long tail
ditinjau untuk penghapusan *hanya* disertai pemeriksaan kanibalisasi. Ganti tolok ukur reorder
tunggal se-perusahaan dengan tolok ukur per aisle.
**Alasan efektif.** Kegagalan ketersediaan pada core staple merusak hubungan berulang, bukan
hanya satu penjualan. Dan tolok ukur tunggal saat ini menandai setiap kategori berkonsumsi
lambat sebagai gagal padahal perilakunya normal.
**Ukuran.** Tingkat ketersediaan stok tertimbang kuadran; reorder rate dipantau sebagai
*simpangan dari rata-rata aisle*, bukan angka absolut.
**Risiko.** Produk ragam rasa (R4, Pola 1) dibeli sebagai satu set — tinjauan profitabilitas
per SKU yang mendorong penghapusan tidak akan menangkap bahwa menghapus satu rasa merusak
rasa-rasa lainnya.

### R6 — Jadwalkan kampanye mengikuti dua puncak akhir pekan yang berbeda bentuk

**Bukti.** Hari 0 dan 1 menyumbang 34,7% minggu, tetapi hari 0 memuncak pukul 13.00–15.00 dengan
basket 11,2 item sedangkan hari 1 memuncak pukul 09.00–11.00 dengan 10,2 item. 64,9% pesanan
jatuh di pukul 09.00–16.00. Pesanan malam (21.00–23.00) hanya 5,3% volume tetapi memiliki basket
terbesar (hingga 11,0 item).
**Aksi.** Dua pengiriman akhir pekan terpisah yang diselaraskan dengan bentuk masing-masing
puncak — pesan belanja besar sebelum siang hari 0, pesan belanja susulan sebelum pagi hari 1.
Jadwalkan kapasitas per jam, bukan per hari: rasio puncak-lembah antar hari hanya 1,41×,
sedangkan antar jam mencapai 53×.
**Alasan efektif.** Satu kampanye akhir pekan akan menyala pada waktu yang salah untuk salah
satu dari dua momen belanja yang berbeda.
**Ukuran.** Konversi buka-ke-pesan menurut jendela pengiriman; ukuran basket menurut jendela.
**Risiko.** Nama hari adalah asumsi — pemetaannya tidak terdokumentasi di sumber. Validasi
terhadap timestamp live sebelum mengalokasikan anggaran pada hari bernama tertentu.

---

## 12. Kesimpulan

Pertanyaan penutup dari brief, dijawab.

**Siapa pelanggan Instacart dan bagaimana perilaku pembelian mereka?** 206.209 pelanggan yang
menempatkan median 10 pesanan berisi median 8 item, dengan ritme mingguan yang terpusat di jam
siang. Mereka terbagi menjadi seperlima pelanggan loyal yang membeli lebih dari separuh volume,
kelompok sering-tapi-ringan, kelompok basket-besar-tapi-jarang, dan sepertiga basis yang tidak
pernah membentuk kebiasaan.

**Produk dan kategori apa yang paling penting?** Produce dari sisi jangkauan (29,2% unit, 74,9%
basket); dairy dari sisi loyalitas (reorder rate 67,0%). 2.537 core staples menyumbang 67,5%
volume pada kelompok yang andal. Pisang adalah produk terpenting menurut setiap ukuran volume —
sekaligus yang paling tidak berguna untuk direkomendasikan.

**Kapan pelanggan paling sering berbelanja?** Pukul 09.00–16.00 (64,9% pesanan), terpusat pada
dua hari akhir pekan yang berbeda bentuk, dengan siklus pengulangan 7 hari.

**Bagaimana pola reorder pelanggan?** 59,0% dari seluruh item. Terbentuk antara pesanan ke-2 dan
ke-6, menumpuk hingga 81,9% pada pesanan ke-50, dan jauh lebih ditentukan oleh seberapa cepat
sebuah kategori habis dikonsumsi ketimbang seberapa disukai produknya.

**Produk apa yang cenderung dibeli bersamaan?** Tiga hal berbeda yang memakai satu nama: varian
rasa satu merek (lift hingga 75,6 — bundel ini), pelengkap resep (lift 3–6 — cross-sell ini),
dan kedekatan kategori (pasta↔saus, rempah→sayur — rancang merchandising di sekitarnya).

**Peluang apa yang muncul, dan apa yang sebaiknya dilakukan perusahaan?** Enam rekomendasi
berbasis bukti di §11, dipimpin oleh langganan replenishment yang dibibitkan dari klaster yang
sudah ber-reorder di atas 84%, dan oleh pemusatan belanja retensi pada jendela pesanan ke-2
hingga ke-6 di mana kurva kebiasaan memang curam.

**Catatan jujur.** Dataset ini tidak memuat harga, margin, tanggal, maupun demografi. Tidak ada
hal di sini yang bisa diubah menjadi proyeksi pendapatan, tidak ada yang bisa diperiksa
musimannya, dan setiap rekomendasi bundel bersyarat pada pemeriksaan margin yang datanya tidak
tersedia. Yang bisa didukung data ini — temuan perilaku, waktu, struktur kategori, dan asosiasi
produk — dinyatakan di atas, dan tidak ada klaim yang melampaui itu.

---

*Analisis oleh notebook 01–06 · dashboard di `dashboard/instacart_dashboard.xlsx` · seluruh
grafik di `reports/figures/` · seluruh tabel pendukung di `reports/tables/`.*
