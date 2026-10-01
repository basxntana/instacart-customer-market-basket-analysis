**Instacart Customer & Market Basket Analysis**

1\. Project Overview

Instacart merupakan platform grocery delivery yang memiliki data
transaksi pelanggan dalam jumlah besar. Data tersebut dapat digunakan
untuk memahami perilaku pembelian customer, performa produk, pola
reorder, serta hubungan antarproduk dalam satu transaksi.\
Dalam project ini, kamu berperan sebagai **Data Analyst** yang bertugas
mengolah dan menganalisis data transaksi Instacart untuk menghasilkan
insight yang dapat membantu perusahaan dalam:

- memahami customer purchasing behavior;

- meningkatkan customer retention;

- memahami performa produk dan kategori;

- mengidentifikasi pola reorder;

- menemukan peluang cross-selling dan product recommendation.

**2. Project Objective**

Analisis harus mampu menjawab pertanyaan utama:

**Bagaimana pola perilaku pembelian customer Instacart, produk apa yang
paling penting bagi customer, dan produk apa yang memiliki peluang untuk
dipasarkan atau direkomendasikan secara bersamaan?**\
Analisis mencakup:

1.  Customer Purchasing Behavior

2.  Order Behavior

3.  Product Performance

4.  Reorder Behavior

5.  Time-Based Purchasing Pattern

6.  Department & Aisle Analysis

7.  Market Basket Analysis

8.  Business Recommendations

**3. Dataset**

Gunakan dataset Instacart berikut:

    orders.csv
    products.csv
    aisles.csv
    departments.csv
    order_products__prior.csv
    order_products__train.csv

**Dataset Relationship**

`                    `┌─────────────┐\
`                    `│` departments `│\
`                    `└──────┬──────┘\
`                           `│\
`                    `┌──────▼──────┐\
`                    `│`   aisles    `│\
`                    `└──────┬──────┘\
`                           `│\
`                    `┌──────▼──────┐\
`                    `│`  products   `│\
`                    `└──────┬──────┘\
`                           `│\
`                           `│\
┌─────────────┐`     `┌──────▼─────────────┐\
│`   orders    `│────▶│` order_products_*   `│\
└─────────────┘`     `└────────────────────┘

**4. Phase 1 — Data Understanding**

Identifikasi dan dokumentasikan:

- Jumlah baris dan kolom setiap dataset

- Nama setiap kolom

- Data type setiap kolom

- Primary key

- Foreign key

- Relationship antar tabel

- Missing values

- Duplicate records

- Invalid values

- Distribusi data

**Deliverables**

- Data Dictionary

- Data Relationship / Data Model

- Initial Data Quality Report

**5. Phase 2 — Data Cleaning**

Lakukan proses data cleaning sesuai kebutuhan.\
Minimal periksa:

- Missing values

- Duplicate data

- Incorrect data types

- Invalid categorical values

- Inconsistent relationships antar tabel

- Outlier yang relevan

- Data yang tidak diperlukan

**Important Rule**

Jangan menghapus data hanya karena terlihat tidak biasa.\
Setiap tindakan cleaning harus memiliki alasan yang jelas dan dapat
dipertanggungjawabkan.\
Contoh:

`days_since_prior_order` memiliki missing value pada first order
customer. Missing value tersebut memiliki makna bisnis sehingga tidak
boleh otomatis dihapus.

**6. Phase 3 — Data Integration**

Gabungkan dataset sesuai kebutuhan analisis.\
Minimal dapat menghubungkan:

`Customer`\
`   `↓\
`Order`\
`   `↓\
`Order Product`\
`   `↓\
`Product`\
`   `↓\
`Aisle`\
`   `↓\
`Department`

Dokumentasikan:

- Tabel yang digunakan

- Jenis join

- Key yang digunakan

- Alasan penggunaan join

- Dampak join terhadap jumlah record

**7. Phase 4 — KPI Analysis**

Buat KPI utama.

**Overall KPI**

- Total Customers

- Total Orders

- Total Products

- Total Items Purchased

- Average Basket Size

- Average Orders per Customer

- Reorder Rate

**Product KPI**

- Most Purchased Products

- Most Reordered Products

- Product Reorder Rate

**Category KPI**

- Top Departments

- Top Aisles

- Department Contribution

- Aisle Contribution

**8. Phase 5 — Customer Analysis**

Analisis perilaku customer.

**8.1 Order Frequency**

Jawab:

- Berapa rata-rata order per customer?

- Bagaimana distribusi jumlah order?

- Berapa customer dengan jumlah order tinggi?

- Apakah terdapat kelompok customer dengan pola order yang berbeda?

**8.2 Basket Size**

Analisis:

- Rata-rata jumlah produk per order

- Distribusi basket size

- Hubungan basket size dengan jumlah order customer

**8.3 Customer Segmentation**

Jika memungkinkan, kelompokkan customer berdasarkan:

    Number of Orders
    Average Basket Size
    Reorder Rate

Jelaskan karakteristik masing-masing segment.

**9. Phase 6 — Time Analysis**

Analisis pola pembelian berdasarkan waktu.

**9.1 Hour**

Identifikasi:

- Jam dengan jumlah order tertinggi

- Jam dengan jumlah order terendah

- Distribusi order sepanjang hari

**9.2 Day of Week**

Identifikasi:

- Hari dengan jumlah order tertinggi

- Hari dengan jumlah order terendah

- Perbedaan pola pembelian berdasarkan hari

**9.3 Days Since Previous Order**

Analisis:

- Rata-rata interval antarorder

- Distribusi interval order

- Hubungan interval order dengan reorder behavior

**10. Phase 7 — Product Analysis**

Identifikasi performa produk.

**10.1 Top Products**

Cari:

- Top 10 produk berdasarkan jumlah pembelian

- Top 10 produk berdasarkan reorder

- Produk dengan reorder rate tertinggi

**10.2 Purchase Volume vs Reorder Rate**

Bandingkan:

    Purchase Volume
            vs
    Reorder Rate

Identifikasi produk yang memiliki:

- High Purchase Volume

- High Reorder Rate

- High Purchase Volume + High Reorder Rate

Jelaskan perbedaan antara produk yang populer dengan produk yang
memiliki customer loyalty tinggi.

**11. Phase 8 — Department & Aisle Analysis**

Analisis performa berdasarkan:

`Department`\
`    `↓\
`Aisle`\
`    `↓\
`Product`

Jawab:

- Department apa yang paling banyak dibeli?

- Aisle apa yang paling populer?

- Department mana yang memiliki reorder rate tertinggi?

- Aisle mana yang memiliki reorder rate tertinggi?

- Apakah kategori tertentu memiliki pola pembelian berulang?

**12. Phase 9 — Reorder Analysis**

Reorder behavior menjadi salah satu fokus utama project.\
Analisis:

`First Purchase`\
`       `↓\
`Repeat Purchase`\
`       `↓\
`Reorder Behavior`

Jawab:

1.  Berapa persentase item yang merupakan reorder?

2.  Produk apa yang paling sering dibeli kembali?

3.  Department mana yang memiliki reorder rate tertinggi?

4.  Apakah reorder behavior berbeda berdasarkan customer order count?

5.  Produk apa yang memiliki kombinasi **High Purchase Volume + High
    Reorder Rate**?

**13. Phase 10 — Market Basket Analysis**

Gunakan **Association Rule Mining** untuk menemukan hubungan antarproduk
dalam satu basket.\
Algoritma yang dapat digunakan:

- Apriori

- FP-Growth

- Association Rules

Library yang dapat digunakan:

    mlxtend

**13.1 Support**

Mengukur seberapa sering kombinasi produk muncul dalam seluruh
transaksi.

**13.2 Confidence**

Mengukur seberapa sering produk B dibeli ketika produk A dibeli.

**13.3 Lift**

Mengukur kekuatan hubungan antara A dan B dibandingkan jika pembelian
terjadi secara independen.

**13.4 Association Rules**

Temukan minimal:

**10 association rules**\
Rule harus memiliki threshold yang ditentukan berdasarkan karakteristik
dataset.\
Dokumentasikan alasan pemilihan:

- Minimum Support

- Minimum Confidence

- Minimum Lift

**Output**

|            |            |         |            |      |
|------------|------------|---------|------------|------|
| Antecedent | Consequent | Support | Confidence | Lift |
| Product A  | Product B  | X%      | X%         | X.XX |

**13.5 Business Interpretation**

Jangan berhenti pada hasil association rules.\
Setiap rule harus dianalisis dari sisi bisnis.\
Contoh:

Produk A dan Produk B sering muncul dalam basket yang sama dan memiliki
lift di atas 1, sehingga terdapat asosiasi positif dalam data
transaksi.\
Jelaskan apakah hubungan tersebut memiliki potensi untuk:

- Cross-selling

- Product recommendation

- Bundle promotion

- Personalized recommendation

**14. Phase 11 — Business Insight**

Setiap insight harus mengikuti struktur:

`Finding`\
`   `↓\
`Evidence`\
`   `↓\
`Business Meaning`

**Contoh**

Finding\
Produk kategori tertentu memiliki reorder rate tinggi.\
**Evidence**\
Reorder rate mencapai X% dan berada di atas rata-rata keseluruhan.\
**Business Meaning**\
Produk tersebut menunjukkan pola pembelian berulang dan berpotensi
menjadi kategori penting dalam strategi customer retention.

**15. Phase 12 — Business Recommendations**

Buat minimal:

**5 business recommendations**\
Rekomendasi dapat mencakup:

- Product recommendation

- Cross-selling

- Personalized recommendation

- Promotion

- Customer retention

- Inventory planning

- Category strategy

**Requirement**

Setiap recommendation **wajib didukung oleh hasil analisis**.\
Jangan membuat rekomendasi yang tidak memiliki evidence dari data.

**16. Visualization Requirements**

Gunakan visualisasi yang sesuai dengan tujuan analisis.

**Time Analysis**

Minimal:

- Orders by Hour

- Orders by Day of Week

**Product Analysis**

Minimal:

- Top Products

- Top Reordered Products

**Category Analysis**

Minimal:

- Department Performance

- Aisle Performance

**Customer Analysis**

Minimal:

- Order Frequency Distribution

- Basket Size Distribution

- Customer Segmentation

**Market Basket Analysis**

Gunakan visualisasi yang relevan untuk menunjukkan hubungan antarproduk
atau association rules.

**17. Dashboard Requirements**

Buat satu dashboard menggunakan:

- Power BI, atau

- Excel

Dashboard minimal memiliki:

┌──────────────────────────────────────────────┐\
│`       INSTACART CUSTOMER ANALYTICS           `│\
├────────┬────────┬────────┬────────┬──────────┤\
│`Customer`│` Orders `│` Items  `│` Basket `│` Reorder  `│\
├────────┴────────┴────────┴────────┴──────────┤\
│`                                              `│\
│`          Order Trend / Time Analysis         `│\
│`                                              `│\
├──────────────────────┬───────────────────────┤\
│` Top Products         `│` Department Analysis   `│\
│`                      `│`                       `│\
├──────────────────────┴───────────────────────┤\
│`          Reorder Analysis                    `│\
├──────────────────────────────────────────────┤\
│`       Market Basket / Product Insights       `│\
└──────────────────────────────────────────────┘

Dashboard harus:

- mudah dibaca;

- memiliki KPI utama;

- memiliki filter yang relevan;

- menggunakan visualisasi yang sesuai;

- menampilkan insight, bukan hanya kumpulan grafik.

**18. Technical Requirements**

Programming Language

    Python

**Required Libraries**

    Pandas
    NumPy
    Matplotlib
    Seaborn
    Scikit-learn

**Market Basket Analysis**

    MLxtend

**Optional Tools**

    SQL
    Power BI
    Excel

Penggunaan SQL sangat disarankan untuk melatih kemampuan Data Analyst.

**19. Project Structure**

Gunakan struktur project berikut:

`instacart-analysis/`\
│\
├──` data/`\
│`   `├──` raw/`\
│`   `└──` processed/`\
│\
├──` notebooks/`\
│`   `├──` 01_data_understanding.ipynb`\
│`   `├──` 02_data_cleaning.ipynb`\
│`   `├──` 03_eda.ipynb`\
│`   `├──` 04_customer_analysis.ipynb`\
│`   `├──` 05_product_analysis.ipynb`\
│`   `└──` 06_market_basket_analysis.ipynb`\
│\
├──` reports/`\
│`   `└──` final_report.pdf`\
│\
├──` dashboard/`\
│`   `└──` instacart_dashboard.pbix`\
│\
└──` README.md`

**20. Final Deliverables**

Pada akhir project, hasil yang dikumpulkan harus terdiri dari:

**20.1 Data Analysis Notebook**

Berisi:

    Data Understanding
    Data Cleaning
    EDA
    Customer Analysis
    Product Analysis
    Reorder Analysis
    Market Basket Analysis

**20.2 Dashboard**

Power BI atau Excel.

**20.3 Final Report**

Struktur:

`Executive Summary`\
`        `↓\
`Business Problem`\
`        `↓\
`Dataset`\
`        `↓\
`Data Preparation`\
`        `↓\
`EDA`\
`        `↓\
`Customer Analysis`\
`        `↓\
`Product Analysis`\
`        `↓\
`Reorder Analysis`\
`        `↓\
`Market Basket Analysis`\
`        `↓\
`Key Findings`\
`        `↓\
`Business Recommendations`\
`        `↓\
`Conclusion`

**20.4 README.md**

README harus menjelaskan:

- Project Overview

- Business Problem

- Dataset

- Data Structure

- Methodology

- Tools

- Key Findings

- Business Recommendations

- Dashboard

- Conclusion

**21. Definition of Done**

Project dianggap selesai apabila analisis mampu menjawab:

**Siapa customer Instacart dan bagaimana perilaku pembelian mereka?**

**Produk dan kategori apa yang paling penting?**

**Kapan customer paling sering melakukan pembelian?**

**Bagaimana pola reorder customer?**

**Produk apa yang cenderung dibeli secara bersamaan?**

**Apa peluang bisnis yang dapat ditemukan dari pola tersebut?**

**Apa rekomendasi yang dapat diberikan kepada perusahaan berdasarkan
evidence dari data?**

**22. Learning Rules**

Project ini dibuat sebagai latihan kemampuan **Data Analyst**, bukan
sekadar latihan coding.\
Workflow yang digunakan:

`Requirement`\
`     `↓\
`Data Understanding`\
`     `↓\
`Kamu Mengerjakan`\
`     `↓\
`Review`\
`     `↓\
`Perbaikan`\
`     `↓\
`Lanjut ke Tahap Berikutnya`

Dalam pengerjaan project:

- Jangan langsung mengikuti notebook Kaggle orang lain.

- Setiap keputusan analisis harus memiliki alasan.

- Jangan membuat visualisasi tanpa pertanyaan yang ingin dijawab.

- Jangan membuat insight tanpa evidence.

- Jangan membuat recommendation tanpa insight.

- Prioritaskan **business reasoning**, bukan hanya kemampuan coding.

**Role**

You: Junior Data Analyst\
**Mentor:** Senior Data Analyst\
Tujuan akhirnya adalah membuat kamu mampu menjelaskan:

**Data → Analysis → Insight → Business Decision**\
bukan hanya:

**Data → Python → Grafik**
