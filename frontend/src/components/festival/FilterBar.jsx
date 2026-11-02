import { useEffect, useState } from "react";
import Button from "../common/Button.jsx";
import Icon from "../common/Icon.jsx";
import { regions } from "../../data/festivals.js";

export default function FilterBar({ query, onChange }) {
  const [keyword, setKeyword] = useState(query.keyword || "");
  const [region, setRegion] = useState(query.area_code || "");
  useEffect(() => {
    setKeyword(query.keyword || "");
    setRegion(query.area_code || "");
  }, [query.keyword, query.area_code]);
  return (
    <form
      className="search"
      role="search"
      aria-label="축제 검색"
      onSubmit={(event) => {
        event.preventDefault();
        onChange({ keyword: keyword.trim(), area_code: region, page: "" });
      }}
    >
      <div className="search-query">
        <Icon name="search" />
        <label className="sr-only" htmlFor="festival-query">
          축제 이름 검색
        </label>
        <input
          id="festival-query"
          type="search"
          placeholder="어떤 축제에서 하루를 보낼까요?"
          value={keyword}
          onChange={(event) => setKeyword(event.target.value)}
        />
      </div>
      <div className="region-field">
        <label htmlFor="festival-region">어디로</label>
        <select
          id="festival-region"
          value={region}
          onChange={(event) => setRegion(event.target.value)}
        >
          <option value="">전국 어디든</option>
          {regions.map(([code, name]) => (
            <option key={code} value={code}>
              {name}
            </option>
          ))}
        </select>
      </div>
      <Button variant="blue" type="submit">
        축제 찾아보기 <Icon name="arrow" />
      </Button>
    </form>
  );
}
