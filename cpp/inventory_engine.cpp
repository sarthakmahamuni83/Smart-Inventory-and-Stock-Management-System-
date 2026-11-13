#include <algorithm>
#include <cmath>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

struct Record {
    string date, store, product, category;
    int inventory = 0, unitsSold = 0, demand = 0;
};

vector<string> splitCSV(const string& line) {
    vector<string> fields;
    string field;
    stringstream ss(line);
    while (getline(ss, field, ',')) fields.push_back(field);
    return fields;
}

int toInt(const string& value) {
    try { return stoi(value); } catch (...) { return 0; }
}

vector<Record> loadLatest(const string& path) {
    ifstream file(path);
    vector<Record> latest;
    if (!file.is_open()) return latest;

    string line;
    getline(file, line); // header
    unordered_map<string, size_t> indexByStoreProduct;

    while (getline(file, line)) {
        vector<string> f = splitCSV(line);
        if (f.size() < 16) continue;

        Record r;
        r.date = f[0];
        r.store = f[1];
        r.product = f[2];
        r.category = f[3];
        r.inventory = toInt(f[5]);
        r.unitsSold = toInt(f[6]);
        r.demand = toInt(f[15]);

        string key = r.store + "|" + r.product;
        auto it = indexByStoreProduct.find(key);
        if (it == indexByStoreProduct.end()) {
            indexByStoreProduct[key] = latest.size();
            latest.push_back(r);
        } else if (r.date > latest[it->second].date) {
            latest[it->second] = r;
        }
    }
    return latest;
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        cerr << "Usage: inventory_engine <search|lowstock|top> <csv_path> [argument]\n";
        return 1;
    }

    string command = argv[1];
    string path = argv[2];
    vector<Record> records = loadLatest(path);

    if (command == "search") {
        if (argc < 4) return 1;
        string productId = argv[3];
        // Hash map: average O(1) product-ID lookup after loading latest records.
        unordered_map<string, vector<Record>> productIndex;
        for (const auto& r : records) productIndex[r.product].push_back(r);

        auto it = productIndex.find(productId);
        if (it == productIndex.end()) return 0;
        for (const auto& r : it->second) {
            cout << r.store << '\t' << r.product << '\t' << r.inventory
                 << '\t' << r.unitsSold << '\t' << r.demand << '\t' << r.date << '\n';
        }
    } else if (command == "lowstock") {
        int threshold = (argc >= 4) ? toInt(argv[3]) : 50;
        vector<Record> low;
        for (const auto& r : records) if (r.inventory <= threshold) low.push_back(r);
        sort(low.begin(), low.end(), [](const Record& a, const Record& b) {
            return a.inventory < b.inventory;
        });
        for (const auto& r : low) {
            cout << r.store << '\t' << r.product << '\t' << r.inventory
                 << '\t' << r.unitsSold << '\t' << r.demand << '\t' << r.date << '\n';
        }
    } else if (command == "top") {
        unordered_map<string, long long> totalSold;
        for (const auto& r : records) totalSold[r.product] += r.unitsSold;
        vector<pair<string, long long>> ranked(totalSold.begin(), totalSold.end());
        sort(ranked.begin(), ranked.end(), [](const auto& a, const auto& b) {
            return a.second > b.second;
        });
        for (const auto& item : ranked) cout << item.first << '\t' << item.second << '\n';
    } else {
        cerr << "Unknown command\n";
        return 1;
    }
    return 0;
}
