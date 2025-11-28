/*******************************************************************************
* Sample ETL Pipeline - Sales Data Processing
* This script demonstrates a typical data processing workflow
*******************************************************************************/

/* Define library references */
LIBNAME raw '/data/raw';
LIBNAME staging '/data/staging';
LIBNAME mart '/data/mart';

/* Set macro variables */
%LET report_date = 2024-01-15;
%LET min_order_value = 100;

/*-----------------------------------------------------------------------------
* Step 1: Load and clean customer data
*-----------------------------------------------------------------------------*/
DATA staging.customers_clean;
    SET raw.customers;

    /* Standardize names */
    first_name = PROPCASE(first_name);
    last_name = PROPCASE(last_name);
    full_name = CATX(' ', first_name, last_name);

    /* Clean email addresses */
    email = LOWCASE(STRIP(email));

    /* Calculate customer tenure */
    tenure_days = INTCK('day', signup_date, TODAY());
    tenure_years = tenure_days / 365.25;

    /* Flag premium customers */
    IF lifetime_value > 10000 THEN premium_flag = 1;
    ELSE premium_flag = 0;

    /* Keep only active customers */
    WHERE status = 'ACTIVE';

    KEEP customer_id first_name last_name full_name email
         signup_date tenure_days tenure_years
         lifetime_value premium_flag segment region;
RUN;

/*-----------------------------------------------------------------------------
* Step 2: Process order transactions
*-----------------------------------------------------------------------------*/
DATA staging.orders_processed;
    SET raw.orders;

    /* Calculate order metrics */
    order_total = quantity * unit_price;
    discount_amount = order_total * (discount_pct / 100);
    net_amount = order_total - discount_amount;

    /* Derive time dimensions */
    order_year = YEAR(order_date);
    order_month = MONTH(order_date);
    order_quarter = QTR(order_date);
    order_weekday = WEEKDAY(order_date);

    /* Flag weekend orders */
    IF order_weekday IN (1, 7) THEN weekend_order = 1;
    ELSE weekend_order = 0;

    /* Filter by minimum order value */
    WHERE net_amount >= &min_order_value;

    DROP discount_pct;
RUN;

/*-----------------------------------------------------------------------------
* Step 3: Load product catalog
*-----------------------------------------------------------------------------*/
DATA staging.products;
    SET raw.product_catalog;

    /* Categorize by price tier */
    IF unit_price < 50 THEN price_tier = 'Budget';
    ELSE IF unit_price < 200 THEN price_tier = 'Standard';
    ELSE price_tier = 'Premium';

    /* Calculate margin */
    margin = (unit_price - cost) / unit_price * 100;

    KEEP product_id product_name category subcategory
         unit_price cost margin price_tier supplier_id;
RUN;

/*-----------------------------------------------------------------------------
* Step 4: Join orders with customers and products
*-----------------------------------------------------------------------------*/
PROC SORT DATA=staging.orders_processed OUT=staging.orders_sorted;
    BY customer_id;
RUN;

PROC SORT DATA=staging.customers_clean OUT=staging.customers_sorted;
    BY customer_id;
RUN;

DATA staging.orders_enriched;
    MERGE staging.orders_sorted (IN=a)
          staging.customers_sorted (IN=b);
    BY customer_id;

    /* Keep only matched records */
    IF a AND b;

    /* Calculate customer-order metrics */
    high_value_order = (net_amount > 500);
RUN;

PROC SORT DATA=staging.orders_enriched;
    BY product_id;
RUN;

PROC SORT DATA=staging.products;
    BY product_id;
RUN;

DATA staging.orders_complete;
    MERGE staging.orders_enriched (IN=a)
          staging.products (IN=b);
    BY product_id;
    IF a;
RUN;

/*-----------------------------------------------------------------------------
* Step 5: Aggregate to customer summary
*-----------------------------------------------------------------------------*/
PROC MEANS DATA=staging.orders_complete NOPRINT;
    CLASS customer_id;
    VAR net_amount quantity;
    OUTPUT OUT=staging.customer_orders_agg
        SUM(net_amount)=total_revenue
        SUM(quantity)=total_items
        MEAN(net_amount)=avg_order_value
        N(order_id)=order_count;
RUN;

DATA mart.customer_summary;
    MERGE staging.customers_clean
          staging.customer_orders_agg (WHERE=(_TYPE_=1) DROP=_TYPE_ _FREQ_);
    BY customer_id;

    /* Calculate additional metrics */
    IF order_count > 0 THEN orders_per_year = order_count / tenure_years;
    ELSE orders_per_year = 0;

    /* Segment customers by behavior */
    IF total_revenue > 5000 AND order_count > 10 THEN customer_tier = 'Gold';
    ELSE IF total_revenue > 1000 OR order_count > 5 THEN customer_tier = 'Silver';
    ELSE customer_tier = 'Bronze';
RUN;

/*-----------------------------------------------------------------------------
* Step 6: Create product performance report
*-----------------------------------------------------------------------------*/
PROC FREQ DATA=staging.orders_complete;
    TABLES category * price_tier / OUT=staging.category_price_freq;
RUN;

PROC MEANS DATA=staging.orders_complete NOPRINT;
    CLASS product_id product_name category;
    VAR net_amount quantity margin;
    OUTPUT OUT=mart.product_performance
        SUM(net_amount)=total_revenue
        SUM(quantity)=units_sold
        MEAN(margin)=avg_margin;
RUN;

/*-----------------------------------------------------------------------------
* Step 7: Generate final reports
*-----------------------------------------------------------------------------*/
PROC PRINT DATA=mart.customer_summary (OBS=100);
    VAR customer_id full_name email total_revenue order_count customer_tier;
    TITLE 'Top Customer Summary';
RUN;

PROC PRINT DATA=mart.product_performance;
    VAR product_name category total_revenue units_sold avg_margin;
    WHERE total_revenue > 10000;
    TITLE 'High Revenue Products';
RUN;
