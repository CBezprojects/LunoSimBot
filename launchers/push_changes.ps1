param(
    [string]$msg = "🔄 Auto commit from push_changes.ps1"
)

cd "C:\Bots\LunoSimBot"

git add .
git commit -m "$msg"
git push origin main
