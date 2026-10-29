import { useEffect, useState } from "react";
import { api } from "./api";

export default function ApiTest() {
  const [status, setStatus] = useState("Checking backend...");

  useEffect(() => {
    api.health()
      .then((data) => setStatus(JSON.stringify(data)))
      .catch((error) => setStatus(`Error: ${error.message}`));
  }, []);

  return (
    <div>
      <h2>Backend Connection Test</h2>
      <pre>{status}</pre>
    </div>
  );
}