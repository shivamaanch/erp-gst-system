// ERP System — Global JS

// Auto-dismiss flash messages
document.addEventListener("DOMContentLoaded", function() {
  setTimeout(function() {
    document.querySelectorAll(".alert-dismissible").forEach(function(el) {
      if (el.classList.contains("alert-success")) {
        new bootstrap.Alert(el).close();
      }
    });
  }, 4000);

  // GSTIN live validator
  document.querySelectorAll("input[data-validate='gstin']").forEach(function(inp) {
    inp.addEventListener("input", function() {
      const val = this.value.trim().toUpperCase();
      this.value = val;
      if (val.length === 15) {
        fetch("/gst/api/verify-gstin?gstin=" + val)
          .then(r => r.json())
          .then(d => {
            this.classList.toggle("is-valid",   d.valid);
            this.classList.toggle("is-invalid", !d.valid);
          });
      } else {
        this.classList.remove("is-valid","is-invalid");
      }
    });
  });

  // Number formatting
  document.querySelectorAll(".currency").forEach(function(el) {
    const v = parseFloat(el.textContent.replace(/,/g,""));
    if (!isNaN(v)) {
      el.textContent = "₹" + v.toLocaleString("en-IN", {minimumFractionDigits:2, maximumFractionDigits:2});
    }
  });
});
