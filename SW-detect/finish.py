
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import scipy.stats as stats

# Read your data
df = pd.read_csv("/Volumes/CSC-Ido/DATA_not_to_be_worked_w_directly/Group_Analysis/group_summary.csv")

# Ensure Group and Condition are categorical
df['Group'] = df['Group'].astype('category')
df['Condition'] = df['Condition'].astype('category')

# Relevel Condition so that "pre-stim" is the baseline
df['Condition'] = df['Condition'].cat.reorder_categories(['pre-stim','stim','post-stim'])

#############################################
# Model for Average_Amplitude
#############################################
model_amp = smf.mixedlm("Average_Amplitude ~ Group * Condition * Protocol",
                        data=df,
                        groups=df["Subject"],
                        re_formula="~Condition")

result_amp = model_amp.fit(method="lbfgs")
print(result_amp.summary())

# Save the summary to a text file
with open("model_average_amplitude_summary.txt", "w") as f:
    f.write(result_amp.summary().as_text())

# Residual plot for Average_Amplitude
plt.figure()
plt.scatter(result_amp.fittedvalues, result_amp.resid)
plt.xlabel("Fitted Values (Amplitude)")
plt.ylabel("Residuals")
plt.title("Residual Plot (Amplitude)")
plt.savefig("residual_plot_amplitude.png", dpi=300)
plt.show()

# Normality check for residuals (Average_Amplitude)
plt.figure()
stats.probplot(result_amp.resid, dist="norm", plot=plt)
plt.title("QQ-Plot Residuals (Amplitude)")
plt.savefig("qqplot_amplitude.png", dpi=300)
plt.show()

#############################################
# Model for Number_of_Waves
#############################################
model_waves = smf.mixedlm("Number_of_Waves ~ Group * Condition * Protocol",
                          data=df,
                          groups=df["Subject"],
                          re_formula="~Condition")

result_waves = model_waves.fit(method="lbfgs")
print(result_waves.summary())

# Save the summary for Number_of_Waves model
with open("model_number_of_waves_summary.txt", "w") as f:
    f.write(result_waves.summary().as_text())

# Residual plot for Number_of_Waves
plt.figure()
plt.scatter(result_waves.fittedvalues, result_waves.resid)
plt.xlabel("Fitted Values (Number of Waves)")
plt.ylabel("Residuals")
plt.title("Residual Plot (Number of Waves)")
plt.savefig("residual_plot_waves.png", dpi=300)
plt.show()

# Normality check for residuals (Number_of_Waves)
plt.figure()
stats.probplot(result_waves.resid, dist="norm", plot=plt)
plt.title("QQ-Plot Residuals (Number of Waves)")
plt.savefig("qqplot_waves.png", dpi=300)
plt.show()

