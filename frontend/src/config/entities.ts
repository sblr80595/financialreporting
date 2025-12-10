/**
 * Entity Configuration
 * ====================
 * 
 * Centralized entity definitions for consistent entity naming across the frontend.
 *
 * IMPORTANT: Backend now reads from config/entities.json (single source of truth).
 * This file is a minimal fallback for types and legacy helpers only.
 * 
 * To keep entities in sync:
 * 1. Update config/entities.json
 * 2. Backend and frontend will consume it through /api/entities
 * 3. This file should not need manual edits for new entities
 */

export interface Entity {
  code: string;        // Internal backend identifier (lowercase)
  name: string;        // Display name for UI
  short_code: string;  // Short code for legacy compatibility
  description?: string;
}

// Fallback entity configuration - intentionally empty so new entities do not require edits here.
// Frontend should rely on /api/entities; this stays for typing/migration helpers.
export const ENTITIES: Entity[] = [];

/**
 * Entity configuration utility class
 */
export class EntityConfig {
  /**
   * Get all configured entities
   */
  static getAllEntities(): Entity[] {
    return [...ENTITIES];
  }

  /**
   * Get entity by code
   */
  static getEntityByCode(code: string): Entity | undefined {
    const codeLower = code.toLowerCase();
    return ENTITIES.find(e => e.code === codeLower);
  }

  /**
   * Get entity by short code
   */
  static getEntityByShortCode(shortCode: string): Entity | undefined {
    return ENTITIES.find(e => e.short_code === shortCode);
  }

  /**
   * Get entity display name by code
   */
  static getEntityName(code: string): string {
    const entity = EntityConfig.getEntityByCode(code);
    return entity ? entity.name : code;
  }

  /**
   * Get entity code from short code
   */
  static getEntityCode(shortCode: string): string {
    const entity = EntityConfig.getEntityByShortCode(shortCode);
    return entity ? entity.code : shortCode.toLowerCase();
  }

  /**
   * Get short code from entity code
   */
  static getShortCode(code: string): string {
    const entity = EntityConfig.getEntityByCode(code);
    return entity ? entity.short_code : code.toUpperCase();
  }

  /**
   * Check if entity code is valid
   */
  static isValidEntity(code: string): boolean {
    return EntityConfig.getEntityByCode(code) !== undefined;
  }

  /**
   * Normalize entity code/name/short_code to standard internal code
   * Handles various input formats
   */
  static normalizeEntityCode(codeOrName: string): string {
    const inputLower = codeOrName.toLowerCase().trim();

    // Handle legacy entity codes (for backward compatibility)
    const legacyMappings: Record<string, string> = {
      'cpm_my': 'cpm',
      'cpm-my': 'cpm',
      'cpmmy': 'cpm',
    };
    if (inputLower in legacyMappings) {
      return legacyMappings[inputLower];
    }

    // Check direct code match
    const byCode = ENTITIES.find(e => e.code === inputLower);
    if (byCode) return byCode.code;

    // Check short code match
    const byShort = ENTITIES.find(e => e.short_code.toLowerCase() === inputLower);
    if (byShort) return byShort.code;

    // Check name match (case-insensitive)
    const byName = ENTITIES.find(e => e.name.toLowerCase() === inputLower);
    if (byName) return byName.code;

    // Default: return lowercase version
    return inputLower;
  }
}

// Export mapping objects for backward compatibility
export const ENTITY_CODE_TO_NAME: Record<string, string> = Object.fromEntries(
  ENTITIES.map(e => [e.code, e.name])
);

export const ENTITY_SHORT_TO_CODE: Record<string, string> = Object.fromEntries(
  ENTITIES.map(e => [e.short_code, e.code])
);

export const ENTITY_CODE_TO_SHORT: Record<string, string> = Object.fromEntries(
  ENTITIES.map(e => [e.code, e.short_code])
);

// Backward compatibility: Legacy entity list format
export const ENTITY_LIST = ENTITIES.map(e => ({
  code: e.short_code,
  name: e.name
}));
