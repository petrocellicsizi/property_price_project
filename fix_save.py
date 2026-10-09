import re

with open('static/js/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix saveInputsToServer definition
old_def = r"async function saveInputsToServer\(profileName\) \{"
new_def = "async function saveInputsToServer(profileName, shouldSaveProfile = true) {"
content = re.sub(old_def, new_def, content)

# Fix the response.ok block inside saveInputsToServer
old_block = r"""            if \(response\.ok\) \{
                showAlert\('Sikeres mentés & AI elemzés!', A\(z\) "\$\{profileName\}" profil sikeresen mentve\., 'success'\);
                if \(result\.gemini_analysis\) \{
                    renderGeminiAnalysis\(result\.gemini_analysis\);
                \}
                if \(result\.gemini_analysis && result\.gemini_analysis\.evaluations\) \{
                    currentAiEvaluations = result\.gemini_analysis\.evaluations;
                \}
                if \(result\.ai_adjusted_suggestions\) \{
                    applyAiAdjustedSuggestionsToUI\(result\.ai_adjusted_suggestions\);
                \}
                
                // Mentsük el LocalStorage-be
                saveProfileToLocal\(profileName, payload, result\.gemini_analysis, result\.ai_adjusted_suggestions\);"""

new_block = """            if (response.ok) {
                if (shouldSaveProfile) {
                    showAlert('Sikeres mentés & AI elemzés!', A(z) "" profil sikeresen mentve., 'success');
                }
                
                if (result.gemini_analysis) {
                    renderGeminiAnalysis(result.gemini_analysis);
                }
                if (result.gemini_analysis && result.gemini_analysis.evaluations) {
                    currentAiEvaluations = result.gemini_analysis.evaluations;
                }
                if (result.ai_adjusted_suggestions) {
                    applyAiAdjustedSuggestionsToUI(result.ai_adjusted_suggestions);
                }
                
                if (shouldSaveProfile) {
                    saveProfileToLocal(profileName, payload, result.gemini_analysis, result.ai_adjusted_suggestions);
                }"""

content = re.sub(old_block, new_block, content)

# Fix btnRunSimulation caller
old_caller = r"saveInputsToServer\('Utolsó szimuláció'\);"
new_caller = "saveInputsToServer('Utolsó szimuláció', false);"
content = re.sub(old_caller, new_caller, content)

with open('static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("app.js patched for save profile logic")
