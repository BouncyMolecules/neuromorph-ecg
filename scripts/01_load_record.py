import wfdb
import matplotlib.pyplot as plt

wfdb.dl_database("mitdb", dl_dir="data/mitdb", records=["100"])

record = wfdb.rdrecord("data/mitdb/100", sampto=3600)
ann = wfdb.rdann("data/mitdb/100", "atr", sampto=3600)

print("Sampling rate:", record.fs)
print("Channels:", record.sig_name)
print("Number of beats:", len(ann.sample))

plt.plot(record.p_signal[:, 0])
plt.plot(ann.sample, record.p_signal[ann.sample, 0], "rx")
plt.title("MIT-BIH record 100, first 10 s")
plt.show()