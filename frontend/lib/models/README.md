# Frontend models ↔ backend src/models

All Dart models in this folder are aligned with backend `backend/src/models` and API response schemas.

| Backend (src/models)         | Frontend (lib/models)                             | API / Notes                                                     |
| ---------------------------- | ------------------------------------------------- | --------------------------------------------------------------- |
| **market.py**                |                                                   |                                                                 |
| `CryptoAsset`                | `CryptoAsset`                                     | Raw asset; API returns `MarketAssetWithLatestPrice`             |
| `MarketData`                 | `MarketData`                                      | Raw price row; API returns `PriceRecordSchema`                  |
| —                            | `MarketAsset`                                     | API view: asset + latest_price, latest_volume, latest_timestamp |
| —                            | `PriceRecord`                                     | API: symbol, price, volume, timestamp                           |
| **analytics.py**             |                                                   |                                                                 |
| `AnalyticsResult`            | `AnalyticsResult`                                 | Stored analytics row                                            |
| —                            | `AnalyticsResponse`, `AssetAnalytics`, `MacdData` | API analytics response                                          |
| **strategy.py**              |                                                   |                                                                 |
| `SignalType` (BUY/SELL/HOLD) | `SignalType`                                      | Enum                                                            |
| `StrategyRun`                | `StrategyRun`                                     | API StrategyRunSchema                                           |
| `StrategySignal`             | `StrategySignal`                                  | API StrategySignalSchema (id, run_id optional)                  |
| **user.py**                  |                                                   |                                                                 |
| `AccountStatus`              | `AccountStatus`                                   | Enum                                                            |
| `KycLevel`                   | `KycLevel`                                        | Enum                                                            |
| `User`                       | `User`                                            | API UserResponse                                                |
| `UserProfile`                | `UserProfile`                                     | API UserProfileResponse                                         |
| `LoginHistory`               | `LoginHistory`                                    | For future auth endpoints                                       |
| `Session`                    | `Session`                                         | For future auth endpoints                                       |

Use `import 'package:frontend/models/models.dart';` (or relative `../models/models.dart`) to get all exports.
