using UnityEngine;
using UnityEngine.Tilemaps;

public class TxtGridTilemapLoader : MonoBehaviour
{
    [Header("Tiles by ID")]
    public TileBase EmptyTile;     // 0
    public TileBase WallTile;      // 1
    public TileBase BushTile;      // 2
    public TileBase SpawnATile;    // 3
    public TileBase SpawnBTile;    // 4
    public TileBase PowerItemTile; // 5

    [Header("Input")]
    public TextAsset TxtMap;       // drag your .txt here
    public bool yZeroAtBottom = true;

    Tilemap tilemap;

    void Awake()
    {
        tilemap = GetComponent<Tilemap>();
        if (!tilemap) Debug.LogError("Attach this script to a Tilemap object (not Grid).");
    }

    void Start()
    {
        if (TxtMap == null) { Debug.LogError("TxtMap not assigned."); return; }
        BuildFromTxt(TxtMap.text);
    }

    void BuildFromTxt(string txt)
    {
        tilemap.ClearAllTiles();

        var lines = txt.Replace("\r", "").Trim().Split('\n');
        int rows = lines.Length;
        if (rows == 0) { Debug.LogError("Empty TXT map."); return; }

        int cols = -1;
        for (int r = 0; r < rows; r++)
        {
            var parts = lines[r].Trim().Split(new char[] { ' ', ',', '\t' }, System.StringSplitOptions.RemoveEmptyEntries);
            if (cols < 0) cols = parts.Length;
            else if (parts.Length != cols) { Debug.LogError($"Row {r} length {parts.Length} != {cols}"); return; }

            int y = yZeroAtBottom ? rows - 1 - r : r;

            for (int c = 0; c < cols; c++)
            {
                if (!int.TryParse(parts[c], out int id)) continue;
                var t = IdToTile(id);
                if (t != null) tilemap.SetTile(new Vector3Int(c, y, 0), t);
            }
        }
        Debug.Log($"Built TXT map: {rows}x{cols}");
    }

    TileBase IdToTile(int id)
    {
        switch (id)
        {
            case 0: return EmptyTile;
            case 1: return WallTile;
            case 2: return BushTile;
            case 3: return SpawnATile;
            case 4: return SpawnBTile;
            case 5: return PowerItemTile;
            default: return null; // unknown id -> skip
        }
    }
}
