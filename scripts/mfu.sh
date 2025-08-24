# Starts the ml flow ui using the correct environment, at the correct location
echo "Navigating to project's root..."
cd "$(dirname "$(dirname "$(realpath "${BASH_SOURCE[0]}")")")"
echo "Navigating to project's root...done"

echo "Activating environment..."
source "$(pwd).13.env/bin/activate"
echo "Activating environment...done"

echo "Launching mlflow ui..."

# --expose-prometheus: This probably won't be used, but it's enabled in case I decide to use it
# --dev TODO: Remove this later
mkdir -p "$(pwd)".mlflow
pushd "$(pwd)".mlflow
# mkdir -p {prometheus,mlflow,artifacts}
mlflow ui \
	--host 127.65.12.247 \
	--port 50222 \
	--backend-store-uri "mlflow" \
	--artifacts-destination "$(pwd)/artifacts" \
	--workers 32 \
	--expose-prometheus "prometheus" \
	--dev
popd
echo "Launching mlflow ui...done"
