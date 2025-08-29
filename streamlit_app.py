#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

#######################
# Page configuration
st.set_page_config(
    page_title="US Population Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("default")

#######################
# CSS styling
st.markdown("""
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

[data-testid="stMetric"] {
    background-color: #393939;
    text-align: center;
    padding: 15px 0;
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

</style>
""", unsafe_allow_html=True)


#######################
# Load data
df_reshaped = pd.read_csv('titanic.csv') ## 분석 데이터 넣기


#######################
# Sidebar
with st.sidebar:
    # ===== 앱 제목 & 데이터 요약 =====
    st.title("🚢 Titanic Survival Dashboard")
    st.caption("Kaggle Titanic 데이터로 생존/탑승 특성 분석")

    # 데이터 기본 정보
    total_rows = len(df_reshaped)
    st.metric(label="Total Records", value=f"{total_rows:,}")

    st.divider()

    # ===== 필터 위젯 =====
    # 선택 옵션 준비
    pclass_options = sorted(df_reshaped["Pclass"].dropna().unique().tolist())
    sex_options = df_reshaped["Sex"].dropna().unique().tolist()
    embarked_options = df_reshaped["Embarked"].dropna().unique().tolist()

    # 범위 계산 (NaN 제외)
    min_age = int(df_reshaped["Age"].min(skipna=True)) if pd.notna(df_reshaped["Age"].min()) else 0
    max_age = int(df_reshaped["Age"].max(skipna=True)) if pd.notna(df_reshaped["Age"].max()) else 80
    min_fare = float(df_reshaped["Fare"].min(skipna=True)) if pd.notna(df_reshaped["Fare"].min()) else 0.0
    max_fare = float(df_reshaped["Fare"].max(skipna=True)) if pd.notna(df_reshaped["Fare"].max()) else 600.0

    # 테마(색상 팔레트/스타일) 선택 – 시각화에서 활용
    theme = st.selectbox(
        "🎨 Chart Theme",
        ["default", "pastel", "vivid", "mono"],
        index=0,
        help="차트 색상/스타일 프리셋 (시각화 섹션에서 적용)"
    )

    # 필터: 클래스/성별/탑승항
    sel_pclass = st.multiselect("🛏️ Pclass (객실 등급)", pclass_options, default=pclass_options)
    sel_sex = st.multiselect("🚻 Sex (성별)", sex_options, default=sex_options)
    sel_embarked = st.multiselect("🛳️ Embarked (탑승항)", embarked_options, default=embarked_options)

    # 필터: 나이/운임
    st.markdown("**Age & Fare Filters**")
    include_age_nan = st.checkbox("나이 결측 포함", value=True)
    age_range = st.slider("Age Range", min_value=min_age, max_value=max_age, value=(min_age, max_age), step=1)
    fare_range = st.slider("Fare Range", min_value=float(min_fare), max_value=float(max_fare),
                           value=(float(min_fare), float(max_fare)), step=0.5)

    # 가족 동반 규모(참고 지표): SibSp + Parch
    if "FamilySize" not in df_reshaped.columns:
        df_reshaped["FamilySize"] = df_reshaped["SibSp"].fillna(0) + df_reshaped["Parch"].fillna(0)
    max_family = int(df_reshaped["FamilySize"].max(skipna=True))
    family_range = st.slider("Family Size (SibSp + Parch)", min_value=0, max_value=max_family,
                             value=(0, max_family), step=1)

    # 리셋 버튼 (세션 상태 초기화)
    if st.button("🔄 Reset Filters"):
        for k in list(st.session_state.keys()):
            if any(key in k for key in ["Pclass", "Sex", "Embarked", "Age Range", "Fare Range", "Family Size", "Chart Theme"]):
                st.session_state.pop(k, None)
        # Streamlit에서 즉시 반영되도록 rerun
        st.rerun()

    st.divider()

    # ===== 필터 적용 =====
    df_filtered = df_reshaped.copy()

    mask_pclass = df_filtered["Pclass"].isin(sel_pclass)
    mask_sex = df_filtered["Sex"].isin(sel_sex)
    mask_embarked = df_filtered["Embarked"].isin(sel_embarked)

    # 나이 조건: 결측 포함 여부 반영
    age_cond = df_filtered["Age"].between(age_range[0], age_range[1], inclusive="both")
    if include_age_nan:
        age_cond = age_cond | df_filtered["Age"].isna()

    fare_cond = df_filtered["Fare"].between(fare_range[0], fare_range[1], inclusive="both")
    family_cond = df_filtered["FamilySize"].between(family_range[0], family_range[1], inclusive="both")

    df_filtered = df_filtered[mask_pclass & mask_sex & mask_embarked & age_cond & fare_cond & family_cond]

    st.success(f"현재 필터 적용 결과: **{len(df_filtered):,} / {total_rows:,}** rows")

    # 추후 본문/차트 영역에서 사용할 수 있도록 세션에 저장
    st.session_state["chart_theme"] = theme
    st.session_state["df_filtered"] = df_filtered



#######################
# Plots



#######################
# Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap='medium')

with col[0]:
    st.subheader("📊 Survival Overview")

    # 필터링된 데이터 불러오기
    df_filtered = st.session_state["df_filtered"]

    # 전체 생존율
    total = len(df_filtered)
    survived = df_filtered["Survived"].sum()
    survival_rate = (survived / total * 100) if total > 0 else 0

    st.metric(
        label="Overall Survival Rate",
        value=f"{survival_rate:.1f}%",
        delta=f"{survived} / {total}"
    )

    st.divider()

    # 성별 생존율
    st.markdown("**성별 생존율**")
    col_gender = st.columns(2)
    for i, sex in enumerate(df_filtered["Sex"].dropna().unique()):
        sub_df = df_filtered[df_filtered["Sex"] == sex]
        cnt = len(sub_df)
        surv = sub_df["Survived"].sum()
        rate = (surv / cnt * 100) if cnt > 0 else 0
        col_gender[i].metric(label=sex.capitalize(), value=f"{rate:.1f}%", delta=f"{surv}/{cnt}")

    st.divider()

    # 클래스별 생존율
    st.markdown("**객실 등급별 생존율 (Pclass)**")
    col_class = st.columns(3)
    for i, pclass in enumerate(sorted(df_filtered["Pclass"].dropna().unique())):
        sub_df = df_filtered[df_filtered["Pclass"] == pclass]
        cnt = len(sub_df)
        surv = sub_df["Survived"].sum()
        rate = (surv / cnt * 100) if cnt > 0 else 0
        col_class[i].metric(label=f"Class {pclass}", value=f"{rate:.1f}%", delta=f"{surv}/{cnt}")



with col[1]:
    st.subheader("📈 Visual Analysis")

    df_filtered = st.session_state["df_filtered"]
    theme = st.session_state.get("chart_theme", "default")

    # ================================
    # 1. 나이 분포 (생존여부별 히스토그램)
    # ================================
    st.markdown("**Age Distribution by Survival**")
    if not df_filtered["Age"].isna().all():
        fig_age = px.histogram(
            df_filtered,
            x="Age",
            color="Survived",
            nbins=20,
            barmode="overlay",
            labels={"Survived": "Survival (0=Dead, 1=Alive)"},
            color_discrete_sequence=px.colors.qualitative.Set2 if theme == "pastel" else px.colors.qualitative.Bold
        )
        st.plotly_chart(fig_age, use_container_width=True)
    else:
        st.info("No Age data available.")

    st.divider()

    # ================================
    # 2. 운임(Fare) vs 생존여부 (박스플롯)
    # ================================
    st.markdown("**Fare vs Survival**")
    fig_fare = px.box(
        df_filtered,
        x="Survived",
        y="Fare",
        points="all",
        labels={"Survived": "Survival (0=Dead, 1=Alive)", "Fare": "Ticket Fare"},
        color="Survived",
        color_discrete_sequence=px.colors.qualitative.Set2 if theme == "pastel" else px.colors.qualitative.Bold
    )
    st.plotly_chart(fig_fare, use_container_width=True)

    st.divider()

    # ================================
    # 3. 탑승항구별 생존율 (막대그래프)
    # ================================
    st.markdown("**Survival Rate by Embarked Port**")
    embarked_summary = (
        df_filtered.groupby("Embarked")["Survived"].mean().reset_index()
    )
    embarked_summary["Survived"] = embarked_summary["Survived"] * 100  # 비율 %

    fig_embarked = px.bar(
        embarked_summary,
        x="Embarked",
        y="Survived",
        text="Survived",
        labels={"Survived": "Survival Rate (%)"},
        color="Embarked",
        color_discrete_sequence=px.colors.qualitative.Set2 if theme == "pastel" else px.colors.qualitative.Bold
    )
    fig_embarked.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    st.plotly_chart(fig_embarked, use_container_width=True)




with col[2]:
    st.subheader("🏆 Rankings & Details")

    df_filtered = st.session_state.get("df_filtered", df_reshaped.copy())
    theme = st.session_state.get("chart_theme", "default")

    # ================================
    # 1) 운임 상위 Top 10 승객
    # ================================
    st.markdown("**Top 10 Passengers by Fare**")
    if "Fare" in df_filtered.columns and not df_filtered.empty:
        top10 = (
            df_filtered.sort_values("Fare", ascending=False)
            .head(10)
            .loc[:, ["Name", "Pclass", "Sex", "Age", "Fare", "Survived", "Embarked"]]
            .copy()
        )
        top10["Survived"] = top10["Survived"].map({1: "Alive", 0: "Dead"})
        # 보기 좋게 정렬/서식
        top10.rename(
            columns={
                "Name": "Passenger",
                "Pclass": "Class",
                "Sex": "Gender",
                "Age": "Age",
                "Fare": "Fare",
                "Embarked": "Port",
            },
            inplace=True,
        )
st.dataframe(top10, use_container_width=True, hide_index=True)

