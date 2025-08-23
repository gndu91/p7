# Starts the ml flow ui using the correct environment, at the correct location
echo "Navigating to project's root..."
cd "$(dirname "$(dirname "$(realpath "${BASH_SOURCE[0]}")")")"
echo "Navigating to project's root...done"

echo "Resetting the mlflow folder..."
echo rm -Irv "$(pwd)".mlflow
rm -Irv "$(pwd)".mlflow
echo "Resetting the mlflow folder...done"
