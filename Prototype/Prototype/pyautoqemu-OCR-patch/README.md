# Patch - Simple OCR for pyautoqemu

With this patch, we enable OCR (using tesseract) in pyautoqemu.

To apply the patch, download [pyautoqemu](https://wiwi-gitlab.uni-muenster.de/itsecurity/pyautoqemu), commit c6fb78365ce71109446f61d755256c3f09c0f56a.

Then apply the patch using the following command:

```$ patch -p1 -d pyautoqemu-main/ < pyautoqemu-OCR.patch```

---

We'd like to thank Katharina de Rentiis for implementing the OCR functionality!
