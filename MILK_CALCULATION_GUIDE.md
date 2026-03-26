# 🥛 Milk Calculation Guide

## 📋 **Understanding Milk Transaction Fields**

### **🔢 What Each Field Means:**

**1. Item Qty (Liters):**
- Quantity of milk in liters
- Example: 100 liters

**2. FAT % (Fat Percentage):**
- Fat content in milk
- Example: 4.0% (4 fat)

**3. CLR % (Color):**
- Color of milk (visual quality indicator)
- Example: 14 (standard white milk color)

**4. Rate per Liter:**
- Price per liter of milk
- Example: ₹50 per liter

**5. SNF % (Solids Not Fat):**
- Other milk solids (proteins, lactose, minerals)
- Example: 8.5% SNF

**6. BF Kgs (Butter Fat Kgs):**
- Actual fat weight in milk
- Formula: `Liters × FAT% ÷ 100`
- Example: 100L × 4.0% ÷ 100 = **4.0 kg fat**

**7. SNF Kgs (Solids Not Fat Kgs):**
- Actual SNF weight in milk
- Formula: `Liters × SNF% ÷ 100`
- Example: 100L × 8.5% ÷ 100 = **8.5 kg SNF**

**8. Ratio 8.50:**
- This is the **SNF to Fat ratio**
- Indicates milk quality
- Formula: `SNF Kgs ÷ Fat Kgs`
- Example: 8.5 ÷ 4.0 = **2.13 ratio**

**9. Final Amount:**
- Total payment for milk
- Formula: `(BF Kgs × Fat Rate) + (SNF Kgs × SNF Rate)`
- Example: (4.0 × ₹200) + (8.5 × ₹100) = **₹1,650**

## 🧮 **Calculation Example**

### **Input Data:**
```
Item Qty: 100 liters
FAT %: 4.0%
CLR %: 14
Rate per Liter: ₹50
SNF %: 8.5%
```

### **Step-by-Step Calculation:**

**Step 1: Calculate Butter Fat Kgs**
```
BF Kgs = 100 × 4.0 ÷ 100 = 4.0 kg
```

**Step 2: Calculate SNF Kgs**
```
SNF Kgs = 100 × 8.5 ÷ 100 = 8.5 kg
```

**Step 3: Calculate Ratio**
```
Ratio = 8.5 ÷ 4.0 = 2.13
```

**Step 4: Calculate Final Amount**
```
Assuming rates from milk rate chart:
- Fat Rate = ₹200 per kg
- SNF Rate = ₹100 per kg

Final Amount = (4.0 × ₹200) + (8.5 × ₹100)
Final Amount = ₹800 + ₹850 = ₹1,650
```

## 🎯 **How System Works**

### **Rate Chart Setup:**
You first create a **Milk Rate Chart** with:
- **Fat Rate:** Price per kg of fat (e.g., ₹200/kg)
- **SNF Rate:** Price per kg of SNF (e.g., ₹100/kg)
- **Base FAT/SNF:** Reference values
- **Effective Date:** When rates apply

### **Transaction Entry:**
When you enter milk transaction:
1. **Enter Quantity, FAT%, SNF%**
2. **System auto-calculates:**
   - BF Kgs = Qty × FAT% ÷ 100
   - SNF Kgs = Qty × SNF% ÷ 100
   - Ratio = SNF Kgs ÷ BF Kgs
3. **System fetches rates** from active rate chart
4. **Calculates final amount** based on actual fat and SNF weights

### **Why This Method:**
- **Fair Pricing:** Pay for actual milk solids, not just volume
- **Quality Based:** Higher FAT% and SNF% = better price
- **Industry Standard:** Standard milk pricing methodology
- **Transparent:** Clear calculation showing component breakdown

## 📊 **Quality Indicators**

### **Good Milk Quality:**
- **FAT %:** 3.5% - 4.5% (cow milk)
- **SNF %:** 8.0% - 9.0% (cow milk)
- **Ratio:** 2.0 - 2.5 (balanced composition)

### **Your Example Analysis:**
```
FAT: 4.0% ✅ Good
SNF: 8.5% ✅ Good  
Ratio: 2.13 ✅ Good quality
```

This indicates **high-quality cow milk** with balanced composition!

## 🎯 **How to Use in System**

### **Step 1: Create Rate Chart**
1. Go to `/milk/rates`
2. Click "Add Rate Chart"
3. Set:
   - Fat Rate: ₹200 per kg
   - SNF Rate: ₹100 per kg
   - Effective Date: Today

### **Step 2: Add Milk Transaction**
1. Go to `/milk/entry`
2. Enter:
   - Party: Select supplier/customer
   - Quantity: 100 (liters)
   - FAT%: 4.0
   - SNF%: 8.5
3. System shows:
   - BF Kgs: 4.0
   - SNF Kgs: 8.5
   - Ratio: 2.13
   - Final Amount: ₹1,650

### **Step 3: Create Invoice (Optional)**
- Check "Create Invoice" to generate bill automatically
- System creates invoice with milk details

## 🔧 **Troubleshooting**

### **If Final Amount Seems Wrong:**
1. **Check Rate Chart:** Verify fat and SNF rates
2. **Verify Percentages:** Ensure FAT% and SNF% are correct
3. **Check Calculations:**
   - BF Kgs = Liters × FAT% ÷ 100
   - SNF Kgs = Liters × SNF% ÷ 100

### **If Ratio Seems Off:**
- **Normal Range:** 2.0 - 2.5 for cow milk
- **High Ratio (>3.0):** May indicate low fat content
- **Low Ratio (<1.8):** May indicate high fat content

---

**🎯 The system calculates payment based on actual milk solids (fat + SNF), not just volume. This ensures fair pricing for milk quality!**
