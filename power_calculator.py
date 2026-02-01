from pc_software.desktop.power_calculator import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.power_calculator", run_name="__main__")


def power(base, exponent):
    """Calculate base raised to the power of exponent"""
    return base ** exponent

class PowerCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Power Calculator")
        self.root.geometry("400x300")
        
        self.create_widgets()
    
    def create_widgets(self):
        tk.Label(self.root, text="Power Calculator", font=("Arial", 16, "bold")).pack(pady=10)
        
        tk.Label(self.root, text="Base:").pack()
        self.base_entry = tk.Entry(self.root)
        self.base_entry.pack(pady=5)
        
        tk.Label(self.root, text="Exponent:").pack()
        self.exponent_entry = tk.Entry(self.root)
        self.exponent_entry.pack(pady=5)
        
        tk.Button(self.root, text="Calculate", command=self.calculate).pack(pady=10)
        
        self.result_label = tk.Label(self.root, text="Result: ", font=("Arial", 12))
        self.result_label.pack(pady=10)
        
        tk.Button(self.root, text="Clear", command=self.clear).pack(pady=5)
    
    def calculate(self):
        try:
            base = float(self.base_entry.get())
            exponent = float(self.exponent_entry.get())
            
            result = power(base, exponent)
            self.result_label.config(text=f"Result: {base}^{exponent} = {result}")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def clear(self):
        self.base_entry.delete(0, tk.END)
        self.exponent_entry.delete(0, tk.END)
        self.result_label.config(text="Result: ")

if __name__ == "__main__":
    root = tk.Tk()
    app = PowerCalculator(root)
    root.mainloop()