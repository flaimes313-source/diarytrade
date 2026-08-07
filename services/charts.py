# services/charts.py
import matplotlib.pyplot as plt
import io
from datetime import datetime
import os

class ChartService:
    @staticmethod
    def create_deposit_chart(deposit_history):
        if len(deposit_history) < 2:
            return None
        
        plt.figure(figsize=(10, 6))
        plt.plot(deposit_history, marker='o', linewidth=2, markersize=4)
        plt.title('График депозита')
        plt.xlabel('Сделка')
        plt.ylabel('Депозит ($)')
        plt.grid(True, alpha=0.3)
        
        # Добавляем начальную и конечную точки
        if deposit_history:
            plt.text(0, deposit_history[0], f'${deposit_history[0]:.2f}', 
                    fontsize=10, ha='right', va='bottom')
            plt.text(len(deposit_history)-1, deposit_history[-1], f'${deposit_history[-1]:.2f}', 
                    fontsize=10, ha='left', va='top')
        
        # Сохраняем в буфер
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        return buf