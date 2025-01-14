
import pandas as pd
import matplotlib.pyplot as plt

# 1. Read the CSV file
df = pd.read_csv('/Users/idohaber/Desktop/group_summary-active.csv')  # <-- Replace with your CSV path

# 2. Group by 'Stage' and sum 'Number_of_Waves'
df_grouped = df.groupby('Stage')['Number_of_Waves'].sum().reset_index()

# 3. Create a bar plot
plt.figure(figsize=(6, 4))
bars = plt.bar(df_grouped['Stage'], df_grouped['Number_of_Waves'], color=['blue', 'orange', 'green'])

# 4. Annotate each bar with the total wave count
for i, bar in enumerate(bars):
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        height,
        str(int(height)),            # Convert height to int for cleaner text
        ha='center', va='bottom'     # Centered horizontally, just above the bar
    )

# Add some labels/titles
plt.title('Total Number of Waves by Stage')
plt.xlabel('Stage')
plt.ylabel('Total Number of Waves')

plt.tight_layout()

# 5. Save the figure
plt.savefig('waves_by_stage.png', dpi=300)
plt.show()

