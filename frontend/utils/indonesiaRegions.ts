export interface RegionCoordinate {
  id: string;
  province: string;
  name: string;
  latitude: number;
  longitude: number;
}

export const INDONESIA_REGIONS: RegionCoordinate[] = [
  // Aceh
  { id: 'aceh-banda-aceh', province: 'Aceh', name: 'Kota Banda Aceh', latitude: 5.54829, longitude: 95.323753 },
  { id: 'aceh-tengah', province: 'Aceh', name: 'Kabupaten Aceh Tengah (Takengon)', latitude: 4.6272, longitude: 96.8481 },
  { id: 'aceh-tenggara', province: 'Aceh', name: 'Kabupaten Aceh Tenggara (Kutacane)', latitude: 3.4922, longitude: 97.8108 },
  { id: 'aceh-gayo-lues', province: 'Aceh', name: 'Kabupaten Gayo Lues (Blangkejeren)', latitude: 3.9814, longitude: 97.3414 },
  { id: 'aceh-pidie', province: 'Aceh', name: 'Kabupaten Pidie (Sigli)', latitude: 5.3849, longitude: 95.9609 },
  { id: 'aceh-barat', province: 'Aceh', name: 'Kabupaten Aceh Barat (Meulaboh)', latitude: 4.1363, longitude: 96.1249 },
  { id: 'aceh-lhokseumawe', province: 'Aceh', name: 'Kota Lhokseumawe', latitude: 5.1801, longitude: 97.1507 },

  // Sumatera Utara
  { id: 'sumut-medan', province: 'Sumatera Utara', name: 'Kota Medan', latitude: 3.595196, longitude: 98.672226 },
  { id: 'sumut-karo', province: 'Sumatera Utara', name: 'Kabupaten Karo (Kabanjahe)', latitude: 3.1003, longitude: 98.4903 },
  { id: 'sumut-simalungun', province: 'Sumatera Utara', name: 'Kabupaten Simalungun / Pematangsiantar', latitude: 2.9604, longitude: 99.0682 },
  { id: 'sumut-taput', province: 'Sumatera Utara', name: 'Kabupaten Tapanuli Utara (Tarutung)', latitude: 2.0258, longitude: 98.9708 },
  { id: 'sumut-madina', province: 'Sumatera Utara', name: 'Kabupaten Mandailing Natal (Panyabungan)', latitude: 0.8588, longitude: 99.5608 },
  { id: 'sumut-toba', province: 'Sumatera Utara', name: 'Kabupaten Toba (Balige)', latitude: 2.3338, longitude: 99.0653 },
  { id: 'sumut-sibolga', province: 'Sumatera Utara', name: 'Kota Sibolga / Tapanuli Tengah', latitude: 1.7406, longitude: 98.7792 },
  { id: 'sumut-nias', province: 'Sumatera Utara', name: 'Kota Gunungsitoli (Nias)', latitude: 1.2833, longitude: 97.6167 },

  // Sumatera Barat
  { id: 'sumbar-padang', province: 'Sumatera Barat', name: 'Kota Padang', latitude: -0.947083, longitude: 100.417181 },
  { id: 'sumbar-bukittinggi', province: 'Sumatera Barat', name: 'Kota Bukittinggi', latitude: -0.3055, longitude: 100.3692 },
  { id: 'sumbar-agam', province: 'Sumatera Barat', name: 'Kabupaten Agam (Lubuk Basung)', latitude: -0.3183, longitude: 100.0319 },
  { id: 'sumbar-tanah-datar', province: 'Sumatera Barat', name: 'Kabupaten Tanah Datar (Batusangkar)', latitude: -0.4547, longitude: 100.5919 },
  { id: 'sumbar-limapuluhkota', province: 'Sumatera Barat', name: 'Kabupaten Lima Puluh Kota (Sarilamak)', latitude: -0.1553, longitude: 100.6789 },
  { id: 'sumbar-solok', province: 'Sumatera Barat', name: 'Kabupaten Solok', latitude: -0.9628, longitude: 100.7856 },
  { id: 'sumbar-pesisir-selatan', province: 'Sumatera Barat', name: 'Kabupaten Pesisir Selatan (Painan)', latitude: -1.3519, longitude: 100.5764 },
  { id: 'sumbar-pasaman-barat', province: 'Sumatera Barat', name: 'Kabupaten Pasaman Barat (Simpang Empat)', latitude: 0.1456, longitude: 99.8406 },

  // Riau
  { id: 'riau-pekanbaru', province: 'Riau', name: 'Kota Pekanbaru', latitude: 0.507068, longitude: 101.447779 },
  { id: 'riau-kampar', province: 'Riau', name: 'Kabupaten Kampar (Bangkinang)', latitude: 0.3361, longitude: 101.0239 },
  { id: 'riau-rokan-hulu', province: 'Riau', name: 'Kabupaten Rokan Hulu (Pasir Pengaraian)', latitude: 0.8586, longitude: 100.3019 },
  { id: 'riau-kuansing', province: 'Riau', name: 'Kabupaten Kuantan Singingi (Teluk Kuantan)', latitude: -0.5311, longitude: 101.5519 },
  { id: 'riau-dumai', province: 'Riau', name: 'Kota Dumai', latitude: 1.667, longitude: 101.45 },

  // Kepulauan Riau
  { id: 'kepri-tanjungpinang', province: 'Kepulauan Riau', name: 'Kota Tanjungpinang', latitude: 0.9186, longitude: 104.4553 },
  { id: 'kepri-batam', province: 'Kepulauan Riau', name: 'Kota Batam', latitude: 1.0456, longitude: 104.0305 },
  { id: 'kepri-natuna', province: 'Kepulauan Riau', name: 'Kabupaten Natuna (Ranai)', latitude: 3.9453, longitude: 108.3831 },

  // Jambi
  { id: 'jambi-kota', province: 'Jambi', name: 'Kota Jambi', latitude: -1.610123, longitude: 103.61312 },
  { id: 'jambi-kerinci', province: 'Jambi', name: 'Kabupaten Kerinci / Sungai Penuh', latitude: -2.0672, longitude: 101.3917 },
  { id: 'jambi-merangin', province: 'Jambi', name: 'Kabupaten Merangin (Bangko)', latitude: -2.0694, longitude: 102.2739 },
  { id: 'jambi-bungo', province: 'Jambi', name: 'Kabupaten Bungo (Muara Bungo)', latitude: -1.4953, longitude: 102.1144 },

  // Sumatera Selatan
  { id: 'sumsel-palembang', province: 'Sumatera Selatan', name: 'Kota Palembang', latitude: -2.976074, longitude: 104.775431 },
  { id: 'sumsel-pagaralam', province: 'Sumatera Selatan', name: 'Kota Pagar Alam', latitude: -4.0222, longitude: 103.2528 },
  { id: 'sumsel-lahat', province: 'Sumatera Selatan', name: 'Kabupaten Lahat', latitude: -3.7889, longitude: 103.5411 },
  { id: 'sumsel-muara-enim', province: 'Sumatera Selatan', name: 'Kabupaten Muara Enim', latitude: -3.6531, longitude: 103.7767 },
  { id: 'sumsel-okus', province: 'Sumatera Selatan', name: 'Kabupaten OKU Selatan (Muaradua)', latitude: -4.5444, longitude: 104.0694 },

  // Kepulauan Bangka Belitung
  { id: 'babel-pangkalpinang', province: 'Kepulauan Bangka Belitung', name: 'Kota Pangkalpinang', latitude: -2.1316, longitude: 106.1169 },
  { id: 'babel-belitung', province: 'Kepulauan Bangka Belitung', name: 'Kabupaten Belitung (Tanjung Pandan)', latitude: -2.7422, longitude: 107.6383 },

  // Bengkulu
  { id: 'bengkulu-kota', province: 'Bengkulu', name: 'Kota Bengkulu', latitude: -3.792845, longitude: 102.260764 },
  { id: 'bengkulu-rejang-lebong', province: 'Bengkulu', name: 'Kabupaten Rejang Lebong (Curup)', latitude: -3.4706, longitude: 102.5214 },
  { id: 'bengkulu-kepahiang', province: 'Bengkulu', name: 'Kabupaten Kepahiang', latitude: -3.6431, longitude: 102.5731 },
  { id: 'bengkulu-lebong', province: 'Bengkulu', name: 'Kabupaten Lebong (Tubei)', latitude: -3.1167, longitude: 102.2167 },

  // Lampung
  { id: 'lampung-bandar-lampung', province: 'Lampung', name: 'Kota Bandar Lampung', latitude: -5.4292, longitude: 105.261 },
  { id: 'lampung-barat', province: 'Lampung', name: 'Kabupaten Lampung Barat (Liwa)', latitude: -5.0258, longitude: 104.0706 },
  { id: 'lampung-tanggamus', province: 'Lampung', name: 'Kabupaten Tanggamus (Kota Agung)', latitude: -5.4894, longitude: 104.6261 },
  { id: 'lampung-selatan', province: 'Lampung', name: 'Kabupaten Lampung Selatan (Kalianda)', latitude: -5.7367, longitude: 105.5964 },

  // DKI Jakarta
  { id: 'jakarta-pusat', province: 'DKI Jakarta', name: 'Jakarta Pusat', latitude: -6.186486, longitude: 106.834091 },
  { id: 'jakarta-selatan', province: 'DKI Jakarta', name: 'Jakarta Selatan', latitude: -6.261493, longitude: 106.8106 },
  { id: 'jakarta-timur', province: 'DKI Jakarta', name: 'Jakarta Timur', latitude: -6.225014, longitude: 106.900447 },
  { id: 'jakarta-barat', province: 'DKI Jakarta', name: 'Jakarta Barat', latitude: -6.167431, longitude: 106.763724 },
  { id: 'jakarta-utara', province: 'DKI Jakarta', name: 'Jakarta Utara', latitude: -6.138414, longitude: 106.863956 },

  // Jawa Barat
  { id: 'jabar-kota-bogor', province: 'Jawa Barat', name: 'Kota Bogor', latitude: -6.597147, longitude: 106.806039 },
  { id: 'jabar-kab-bogor', province: 'Jawa Barat', name: 'Kabupaten Bogor (Cibinong / Puncak)', latitude: -6.4816, longitude: 106.8542 },
  { id: 'jabar-kota-bandung', province: 'Jawa Barat', name: 'Kota Bandung', latitude: -6.917464, longitude: 107.619123 },
  { id: 'jabar-kab-bandung', province: 'Jawa Barat', name: 'Kabupaten Bandung (Soreang)', latitude: -7.0247, longitude: 107.5197 },
  { id: 'jabar-kbb', province: 'Jawa Barat', name: 'Kabupaten Bandung Barat (Ngamprah / Lembang)', latitude: -6.8428, longitude: 107.5086 },
  { id: 'jabar-cianjur', province: 'Jawa Barat', name: 'Kabupaten Cianjur', latitude: -6.8208, longitude: 107.1425 },
  { id: 'jabar-sukabumi', province: 'Jawa Barat', name: 'Kabupaten Sukabumi (Pelabuhanratu)', latitude: -6.9875, longitude: 106.5506 },
  { id: 'jabar-garut', province: 'Jawa Barat', name: 'Kabupaten Garut', latitude: -7.227906, longitude: 107.908699 },
  { id: 'jabar-sumedang', province: 'Jawa Barat', name: 'Kabupaten Sumedang', latitude: -6.8586, longitude: 107.9214 },
  { id: 'jabar-tasikmalaya', province: 'Jawa Barat', name: 'Kabupaten Tasikmalaya (Singaparna)', latitude: -7.3519, longitude: 108.1114 },
  { id: 'jabar-majalengka', province: 'Jawa Barat', name: 'Kabupaten Majalengka', latitude: -6.8364, longitude: 108.2278 },
  { id: 'jabar-kuningan', province: 'Jawa Barat', name: 'Kabupaten Kuningan', latitude: -6.9764, longitude: 108.4847 },
  { id: 'jabar-subang', province: 'Jawa Barat', name: 'Kabupaten Subang', latitude: -6.5714, longitude: 107.7586 },
  { id: 'jabar-purwakarta', province: 'Jawa Barat', name: 'Kabupaten Purwakarta', latitude: -6.5569, longitude: 107.4433 },
  { id: 'jabar-ciamis', province: 'Jawa Barat', name: 'Kabupaten Ciamis', latitude: -7.3261, longitude: 108.3536 },

  // Banten
  { id: 'banten-serang', province: 'Banten', name: 'Kota Serang', latitude: -6.120002, longitude: 106.150276 },
  { id: 'banten-lebak', province: 'Banten', name: 'Kabupaten Lebak (Rangkasbitung)', latitude: -6.3578, longitude: 106.2489 },
  { id: 'banten-pandeglang', province: 'Banten', name: 'Kabupaten Pandeglang', latitude: -6.3089, longitude: 106.1067 },
  { id: 'banten-tangerang', province: 'Banten', name: 'Kota Tangerang', latitude: -6.1702, longitude: 106.6403 },

  // Jawa Tengah
  { id: 'jateng-semarang', province: 'Jawa Tengah', name: 'Kota Semarang', latitude: -6.966667, longitude: 110.416664 },
  { id: 'jateng-banjarnegara', province: 'Jawa Tengah', name: 'Kabupaten Banjarnegara', latitude: -7.3976, longitude: 109.6967 },
  { id: 'jateng-wonosobo', province: 'Jawa Tengah', name: 'Kabupaten Wonosobo', latitude: -7.3631, longitude: 109.9006 },
  { id: 'jateng-banyumas', province: 'Jawa Tengah', name: 'Kabupaten Banyumas (Purwokerto)', latitude: -7.4244, longitude: 109.2302 },
  { id: 'jateng-purbalingga', province: 'Jawa Tengah', name: 'Kabupaten Purbalingga', latitude: -7.3881, longitude: 109.3636 },
  { id: 'jateng-kebumen', province: 'Jawa Tengah', name: 'Kabupaten Kebumen', latitude: -7.6694, longitude: 109.6519 },
  { id: 'jateng-purworejo', province: 'Jawa Tengah', name: 'Kabupaten Purworejo', latitude: -7.7128, longitude: 110.0086 },
  { id: 'jateng-magelang', province: 'Jawa Tengah', name: 'Kabupaten Magelang (Mungkid)', latitude: -7.5567, longitude: 110.2206 },
  { id: 'jateng-temanggung', province: 'Jawa Tengah', name: 'Kabupaten Temanggung', latitude: -7.3164, longitude: 110.1753 },
  { id: 'jateng-karanganyar', province: 'Jawa Tengah', name: 'Kabupaten Karanganyar', latitude: -7.5964, longitude: 110.9506 },
  { id: 'jateng-cilacap', province: 'Jawa Tengah', name: 'Kabupaten Cilacap', latitude: -7.7278, longitude: 109.0086 },
  { id: 'jateng-brebes', province: 'Jawa Tengah', name: 'Kabupaten Brebes', latitude: -6.8711, longitude: 109.0422 },
  { id: 'jateng-pekalongan', province: 'Jawa Tengah', name: 'Kabupaten Pekalongan (Kajen)', latitude: -7.0289, longitude: 109.5931 },

  // DI Yogyakarta
  { id: 'diy-yogyakarta', province: 'DI Yogyakarta', name: 'Kota Yogyakarta', latitude: -7.79558, longitude: 110.36949 },
  { id: 'diy-kulonprogo', province: 'DI Yogyakarta', name: 'Kabupaten Kulon Progo (Wates)', latitude: -7.8569, longitude: 110.1586 },
  { id: 'diy-gunungkidul', province: 'DI Yogyakarta', name: 'Kabupaten Gunungkidul (Wonosari)', latitude: -7.9669, longitude: 110.6025 },
  { id: 'diy-bantul', province: 'DI Yogyakarta', name: 'Kabupaten Bantul', latitude: -7.8878, longitude: 110.3289 },
  { id: 'diy-sleman', province: 'DI Yogyakarta', name: 'Kabupaten Sleman', latitude: -7.7167, longitude: 110.3556 },

  // Jawa Timur
  { id: 'jatim-surabaya', province: 'Jawa Timur', name: 'Kota Surabaya', latitude: -7.257472, longitude: 112.75209 },
  { id: 'jatim-malang', province: 'Jawa Timur', name: 'Kabupaten Malang (Kepanjen)', latitude: -8.1306, longitude: 112.5728 },
  { id: 'jatim-batu', province: 'Jawa Timur', name: 'Kota Batu', latitude: -7.8671, longitude: 112.5239 },
  { id: 'jatim-trenggalek', province: 'Jawa Timur', name: 'Kabupaten Trenggalek', latitude: -8.0503, longitude: 111.7069 },
  { id: 'jatim-ponorogo', province: 'Jawa Timur', name: 'Kabupaten Ponorogo', latitude: -7.8686, longitude: 111.4622 },
  { id: 'jatim-pacitan', province: 'Jawa Timur', name: 'Kabupaten Pacitan', latitude: -8.1944, longitude: 111.1053 },
  { id: 'jatim-nganjuk', province: 'Jawa Timur', name: 'Kabupaten Nganjuk', latitude: -7.605, longitude: 111.9036 },
  { id: 'jatim-lumajang', province: 'Jawa Timur', name: 'Kabupaten Lumajang', latitude: -8.1336, longitude: 113.2244 },
  { id: 'jatim-jember', province: 'Jawa Timur', name: 'Kabupaten Jember', latitude: -8.1722, longitude: 113.6997 },
  { id: 'jatim-bondowoso', province: 'Jawa Timur', name: 'Kabupaten Bondowoso', latitude: -7.9136, longitude: 113.8214 },
  { id: 'jatim-banyuwangi', province: 'Jawa Timur', name: 'Kabupaten Banyuwangi', latitude: -8.2192, longitude: 114.3692 },

  // Bali
  { id: 'bali-denpasar', province: 'Bali', name: 'Kota Denpasar', latitude: -8.670458, longitude: 115.212629 },
  { id: 'bali-bangli', province: 'Bali', name: 'Kabupaten Bangli (Kintamani)', latitude: -8.4547, longitude: 115.3547 },
  { id: 'bali-karangasem', province: 'Bali', name: 'Kabupaten Karangasem (Amlapura)', latitude: -8.4481, longitude: 115.6128 },
  { id: 'bali-buleleng', province: 'Bali', name: 'Kabupaten Buleleng (Singaraja)', latitude: -8.1128, longitude: 115.0881 },
  { id: 'bali-tabanan', province: 'Bali', name: 'Kabupaten Tabanan', latitude: -8.5414, longitude: 115.1253 },

  // Nusa Tenggara Barat
  { id: 'ntb-mataram', province: 'Nusa Tenggara Barat', name: 'Kota Mataram', latitude: -8.583333, longitude: 116.116667 },
  { id: 'ntb-lombok-utara', province: 'Nusa Tenggara Barat', name: 'Kabupaten Lombok Utara (Tanjung)', latitude: -8.3536, longitude: 116.1569 },
  { id: 'ntb-lombok-timur', province: 'Nusa Tenggara Barat', name: 'Kabupaten Lombok Timur (Selong)', latitude: -8.6519, longitude: 116.5381 },
  { id: 'ntb-sumbawa', province: 'Nusa Tenggara Barat', name: 'Kabupaten Sumbawa (Sumbawa Besar)', latitude: -8.4931, longitude: 117.4203 },
  { id: 'ntb-bima', province: 'Nusa Tenggara Barat', name: 'Kota Bima', latitude: -8.46, longitude: 118.7267 },

  // Nusa Tenggara Timur
  { id: 'ntt-kupang', province: 'Nusa Tenggara Timur', name: 'Kota Kupang', latitude: -10.1772, longitude: 123.607 },
  { id: 'ntt-manggarai', province: 'Nusa Tenggara Timur', name: 'Kabupaten Manggarai (Ruteng)', latitude: -8.6131, longitude: 120.4644 },
  { id: 'ntt-manggarai-barat', province: 'Nusa Tenggara Timur', name: 'Kabupaten Manggarai Barat (Labuan Bajo)', latitude: -8.4964, longitude: 119.8878 },
  { id: 'ntt-ende', province: 'Nusa Tenggara Timur', name: 'Kabupaten Ende', latitude: -8.8433, longitude: 121.6622 },
  { id: 'ntt-sikka', province: 'Nusa Tenggara Timur', name: 'Kabupaten Sikka (Maumere)', latitude: -8.6214, longitude: 122.2122 },
  { id: 'ntt-flores-timur', province: 'Nusa Tenggara Timur', name: 'Kabupaten Flores Timur (Larantuka)', latitude: -8.3458, longitude: 122.9806 },

  // Kalimantan Barat
  { id: 'kalbar-pontianak', province: 'Kalimantan Barat', name: 'Kota Pontianak', latitude: -0.02633, longitude: 109.342504 },
  { id: 'kalbar-kapuas-hulu', province: 'Kalimantan Barat', name: 'Kabupaten Kapuas Hulu (Putussibau)', latitude: 0.8586, longitude: 112.9269 },
  { id: 'kalbar-sintang', province: 'Kalimantan Barat', name: 'Kabupaten Sintang', latitude: 0.0681, longitude: 111.4981 },
  { id: 'kalbar-singkawang', province: 'Kalimantan Barat', name: 'Kota Singkawang', latitude: 0.9092, longitude: 108.9847 },

  // Kalimantan Tengah
  { id: 'kalteng-palangkaraya', province: 'Kalimantan Tengah', name: 'Kota Palangka Raya', latitude: -2.2136, longitude: 113.9108 },
  { id: 'kalteng-sampit', province: 'Kalimantan Tengah', name: 'Kabupaten Kotawaringin Timur (Sampit)', latitude: -2.5361, longitude: 112.9506 },
  { id: 'kalteng-pangkalanbun', province: 'Kalimantan Tengah', name: 'Kabupaten Kotawaringin Barat (Pangkalan Bun)', latitude: -2.6833, longitude: 111.6167 },
  { id: 'kalteng-murung-raya', province: 'Kalimantan Tengah', name: 'Kabupaten Murung Raya (Puruk Cahu)', latitude: -0.6256, longitude: 114.5731 },

  // Kalimantan Selatan
  { id: 'kalsel-banjarmasin', province: 'Kalimantan Selatan', name: 'Kota Banjarmasin', latitude: -3.3186, longitude: 114.5944 },
  { id: 'kalsel-banjarbaru', province: 'Kalimantan Selatan', name: 'Kota Banjarbaru', latitude: -3.4439, longitude: 114.8303 },
  { id: 'kalsel-banjar', province: 'Kalimantan Selatan', name: 'Kabupaten Banjar (Martapura)', latitude: -3.4108, longitude: 114.8475 },
  { id: 'kalsel-kotabaru', province: 'Kalimantan Selatan', name: 'Kabupaten Kotabaru', latitude: -3.2378, longitude: 116.2289 },

  // Kalimantan Timur
  { id: 'kaltim-samarinda', province: 'Kalimantan Timur', name: 'Kota Samarinda', latitude: -0.502106, longitude: 117.153709 },
  { id: 'kaltim-balikpapan', province: 'Kalimantan Timur', name: 'Kota Balikpapan', latitude: -1.2379, longitude: 116.8529 },
  { id: 'kaltim-kukar', province: 'Kalimantan Timur', name: 'Kabupaten Kutai Kartanegara (Tenggarong)', latitude: -0.4139, longitude: 116.9894 },
  { id: 'kaltim-berau', province: 'Kalimantan Timur', name: 'Kabupaten Berau (Tanjung Redeb)', latitude: 2.1558, longitude: 117.4969 },

  // Kalimantan Utara
  { id: 'kaltara-tanjung-selor', province: 'Kalimantan Utara', name: 'Kabupaten Bulungan (Tanjung Selor)', latitude: 2.8375, longitude: 117.3653 },
  { id: 'kaltara-tarakan', province: 'Kalimantan Utara', name: 'Kota Tarakan', latitude: 3.3, longitude: 117.6333 },
  { id: 'kaltara-malinau', province: 'Kalimantan Utara', name: 'Kabupaten Malinau', latitude: 3.5836, longitude: 116.6386 },

  // Sulawesi Utara
  { id: 'sulut-manado', province: 'Sulawesi Utara', name: 'Kota Manado', latitude: 1.47483, longitude: 124.842079 },
  { id: 'sulut-tomohon', province: 'Sulawesi Utara', name: 'Kota Tomohon', latitude: 1.3236, longitude: 124.8403 },
  { id: 'sulut-minahasa', province: 'Sulawesi Utara', name: 'Kabupaten Minahasa (Tondano)', latitude: 1.3006, longitude: 124.9114 },
  { id: 'sulut-bitung', province: 'Sulawesi Utara', name: 'Kota Bitung', latitude: 1.4404, longitude: 125.1217 },
  { id: 'sulut-sangihe', province: 'Sulawesi Utara', name: 'Kabupaten Kepulauan Sangihe (Tahuna)', latitude: 3.6064, longitude: 125.4953 },

  // Gorontalo
  { id: 'gorontalo-kota', province: 'Gorontalo', name: 'Kota Gorontalo', latitude: 0.543544, longitude: 123.056769 },
  { id: 'gorontalo-bone-bolango', province: 'Gorontalo', name: 'Kabupaten Bone Bolango (Suwawa)', latitude: 0.5453, longitude: 123.1444 },
  { id: 'gorontalo-pohuwato', province: 'Gorontalo', name: 'Kabupaten Pohuwato (Marisa)', latitude: 0.4686, longitude: 121.9444 },

  // Sulawesi Tengah
  { id: 'sulteng-palu', province: 'Sulawesi Tengah', name: 'Kota Palu', latitude: -0.8917, longitude: 119.8707 },
  { id: 'sulteng-sigi', province: 'Sulawesi Tengah', name: 'Kabupaten Sigi', latitude: -1.1167, longitude: 119.9333 },
  { id: 'sulteng-donggala', province: 'Sulawesi Tengah', name: 'Kabupaten Donggala', latitude: -0.6744, longitude: 119.7447 },
  { id: 'sulteng-poso', province: 'Sulawesi Tengah', name: 'Kabupaten Poso', latitude: -1.3958, longitude: 120.7525 },
  { id: 'sulteng-parimo', province: 'Sulawesi Tengah', name: 'Kabupaten Parigi Moutong', latitude: -0.8167, longitude: 120.1667 },

  // Sulawesi Barat
  { id: 'sulbar-mamuju', province: 'Sulawesi Barat', name: 'Kabupaten Mamuju', latitude: -2.677, longitude: 118.887 },
  { id: 'sulbar-mamasa', province: 'Sulawesi Barat', name: 'Kabupaten Mamasa', latitude: -2.9369, longitude: 119.3731 },
  { id: 'sulbar-polman', province: 'Sulawesi Barat', name: 'Kabupaten Polewali Mandar', latitude: -3.4325, longitude: 119.3436 },
  { id: 'sulbar-majene', province: 'Sulawesi Barat', name: 'Kabupaten Majene', latitude: -3.5403, longitude: 118.9706 },

  // Sulawesi Selatan
  { id: 'sulsel-makassar', province: 'Sulawesi Selatan', name: 'Kota Makassar', latitude: -5.147665, longitude: 119.432731 },
  { id: 'sulsel-gowa', province: 'Sulawesi Selatan', name: 'Kabupaten Gowa (Sungguminasa)', latitude: -5.2067, longitude: 119.4525 },
  { id: 'sulsel-tana-toraja', province: 'Sulawesi Selatan', name: 'Kabupaten Tana Toraja (Makale)', latitude: -3.1036, longitude: 119.8525 },
  { id: 'sulsel-toraja-utara', province: 'Sulawesi Selatan', name: 'Kabupaten Toraja Utara (Rantepao)', latitude: -2.9711, longitude: 119.8981 },
  { id: 'sulsel-luwu', province: 'Sulawesi Selatan', name: 'Kabupaten Luwu (Belopa)', latitude: -3.3833, longitude: 120.3667 },
  { id: 'sulsel-luwu-utara', province: 'Sulawesi Selatan', name: 'Kabupaten Luwu Utara (Masamba)', latitude: -2.5567, longitude: 120.3236 },
  { id: 'sulsel-enrekang', province: 'Sulawesi Selatan', name: 'Kabupaten Enrekang', latitude: -3.5625, longitude: 119.7753 },

  // Sulawesi Tenggara
  { id: 'sultra-kendari', province: 'Sulawesi Tenggara', name: 'Kota Kendari', latitude: -3.99846, longitude: 122.512974 },
  { id: 'sultra-kolaka', province: 'Sulawesi Tenggara', name: 'Kabupaten Kolaka', latitude: -4.0608, longitude: 121.6003 },
  { id: 'sultra-baubau', province: 'Sulawesi Tenggara', name: 'Kota Baubau', latitude: -5.4631, longitude: 122.6056 },

  // Maluku
  { id: 'maluku-ambon', province: 'Maluku', name: 'Kota Ambon', latitude: -3.6954, longitude: 128.1814 },
  { id: 'maluku-tengah', province: 'Maluku', name: 'Kabupaten Maluku Tengah (Masohi)', latitude: -3.2975, longitude: 128.9581 },
  { id: 'maluku-sbb', province: 'Maluku', name: 'Kabupaten Seram Bagian Barat (Piru)', latitude: -3.0631, longitude: 128.1886 },

  // Maluku Utara
  { id: 'malut-ternate', province: 'Maluku Utara', name: 'Kota Ternate', latitude: 0.7893, longitude: 127.3831 },
  { id: 'malut-sofifi', province: 'Maluku Utara', name: 'Sofifi (Tidore Kepulauan)', latitude: 0.7375, longitude: 127.5583 },
  { id: 'malut-halbar', province: 'Maluku Utara', name: 'Kabupaten Halmahera Barat (Jailolo)', latitude: 1.0731, longitude: 127.4753 },

  // Papua
  { id: 'papua-jayapura', province: 'Papua', name: 'Kota Jayapura', latitude: -2.5916, longitude: 140.669 },
  { id: 'papua-sentani', province: 'Papua', name: 'Kabupaten Jayapura (Sentani)', latitude: -2.5706, longitude: 140.5175 },
  { id: 'papua-biak', province: 'Papua', name: 'Kabupaten Biak Numfor', latitude: -1.1767, longitude: 136.0819 },

  // Papua Barat
  { id: 'pabar-manokwari', province: 'Papua Barat', name: 'Kabupaten Manokwari', latitude: -0.8615, longitude: 134.062 },
  { id: 'pabar-fakfak', province: 'Papua Barat', name: 'Kabupaten Fakfak', latitude: -2.9261, longitude: 132.2978 },

  // Papua Barat Daya
  { id: 'pbd-sorong', province: 'Papua Barat Daya', name: 'Kota Sorong', latitude: -0.8762, longitude: 131.2558 },
  { id: 'pbd-raja-ampat', province: 'Papua Barat Daya', name: 'Kabupaten Raja Ampat (Waisai)', latitude: -0.4314, longitude: 130.8225 },

  // Papua Tengah
  { id: 'pateng-nabire', province: 'Papua Tengah', name: 'Kabupaten Nabire', latitude: -3.3636, longitude: 135.5014 },
  { id: 'pateng-mimika', province: 'Papua Tengah', name: 'Kabupaten Mimika (Timika)', latitude: -4.5467, longitude: 136.8833 },

  // Papua Pegunungan
  { id: 'papeg-jayawijaya', province: 'Papua Pegunungan', name: 'Kabupaten Jayawijaya (Wamena)', latitude: -4.0989, longitude: 138.9436 },
  { id: 'papeg-yahukimo', province: 'Papua Pegunungan', name: 'Kabupaten Yahukimo (Dekai)', latitude: -4.855, longitude: 139.4833 },

  // Papua Selatan
  { id: 'pasel-merauke', province: 'Papua Selatan', name: 'Kabupaten Merauke', latitude: -8.4932, longitude: 140.4018 },
];

export const INDONESIA_PROVINCES: string[] = Array.from(
  new Set(INDONESIA_REGIONS.map((region) => region.province))
);
