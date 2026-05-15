/**
 * Version helper for office-addin
 * Reads from the centralized VERSION file at repository root.
 * This ensures the office-addin version stays in sync with desktop and web components.
 */

import * as fs from "fs";
import * as path from "path";

export function getVersion(): string {
  try {
    // From office-addin/src/version.ts, VERSION is at ../../VERSION
    const versionFilePath = path.join(__dirname, "../../VERSION");
    const versionContent = fs.readFileSync(versionFilePath, "utf-8");
    return versionContent.trim();
  } catch (error) {
    console.warn("Could not read VERSION file, falling back to package.json", error);
    // Fallback to reading from package.json if VERSION file not found
    try {
      const packageJsonPath = path.join(__dirname, "../package.json");
      const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, "utf-8"));
      return packageJson.version || "7.2.0";
    } catch {
      return "7.2.0";
    }
  }
}

export default getVersion();
